"""
Regression test suite for Drain3 log parsing and block association.

Verifies the fix for generic non-HDFS application logs:
1. Exact 12-line sample verification with session_id="logsage-exact-regression-001" and threshold=0.
2. Proper header & level extraction (ISO timestamp, severity levels).
3. Preservation of real HDFS block IDs and non-attribution of fake HDFS blocks to generic logs.
4. Correct grouping of repeated log patterns into namespaced cluster groups.
5. Correct feature extraction and block counts in BlockFeatureExtractor.
6. End-to-end PipelineService execution creating incidents for anomalous blocks.
"""
from __future__ import annotations

import asyncio
import json
import unittest

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from backend.db.database import Base
from backend.db.models import LogEntry, Incident, IncidentSeverity
from backend.services.pipeline_service import PipelineService
from ml.parser.drain_parser import DrainParser, ParseResult
from ml.preprocessing.feature_extraction import BlockFeatureExtractor


SAMPLE_APP_LOGS = [
    "2026-11-19 10:00:01 INFO Database connection established",
    "2026-11-19 10:00:02 INFO User service started",
    "2026-11-19 10:00:03 ERROR Database connection timeout after 30s",
    "2026-11-19 10:00:04 ERROR Database connection timeout after 30s",
    "2026-11-19 10:00:05 ERROR Connection pool exhausted",
    "2026-11-19 10:00:06 ERROR Connection pool exhausted",
    "2026-11-19 10:00:07 ERROR Failed to execute database query",
    "2026-11-19 10:00:08 ERROR Failed to execute database query",
    "2026-11-19 10:00:09 WARN Database retry attempt 1",
    "2026-11-19 10:00:10 WARN Database retry attempt 2",
    "2026-11-19 10:00:11 ERROR Database connection timeout after 30s",
    "2026-11-19 10:00:12 ERROR Connection pool exhausted",
]


class TestDrainParserBlockAssociation(unittest.TestCase):
    """Unit tests for DrainParser block ID assignment and metadata extraction."""

    def setUp(self):
        self.parser = DrainParser()

    def test_parse_sample_logs_count_and_fields(self):
        """Verify all 12 lines are parsed with valid templates, levels, and grouping IDs."""
        results = self.parser.parse_lines(SAMPLE_APP_LOGS, update_model=True)
        self.assertEqual(len(results), 12)

        for res in results:
            self.assertIsInstance(res, ParseResult)
            self.assertIsNotNone(res.timestamp, f"Timestamp is None for line {res.line_id}")
            self.assertIsNotNone(res.level, f"Level is None for line {res.line_id}")
            self.assertIn(res.level, ("INFO", "WARN", "ERROR"))
            # Generic logs do not have HDFS block IDs
            self.assertIsNone(res.block_id, f"block_id should be None for non-HDFS line {res.line_id}")
            self.assertEqual(res.block_ids, [])
            # Grouping ID uses clearly distinguished cluster namespace
            self.assertTrue(res.group_id.startswith("cluster_E"))
            self.assertTrue(res.event_id.startswith("E"))
            self.assertTrue(len(res.event_template) > 0)
            self.assertFalse(res.is_malformed)

            # Dictionary representation checks
            d = res.to_dict()
            self.assertIn("block_id", d)
            self.assertIn("block_ids", d)
            self.assertIn("group_id", d)
            self.assertIsNone(d["block_id"])
            self.assertEqual(d["block_ids"], [])
            self.assertEqual(d["group_id"], res.group_id)

    def test_repeated_patterns_share_cluster_group_and_template(self):
        """Verify repeated log patterns receive identical event IDs and grouping IDs."""
        results = self.parser.parse_lines(SAMPLE_APP_LOGS, update_model=True)

        # Lines 3, 4, 11: "Database connection timeout after 30s"
        r3, r4, r11 = results[2], results[3], results[10]
        self.assertEqual(r3.event_id, r4.event_id)
        self.assertEqual(r4.event_id, r11.event_id)
        self.assertEqual(r3.group_id, r4.group_id)
        self.assertEqual(r4.group_id, r11.group_id)
        self.assertEqual(r3.event_template, "Database connection timeout after 30s")

        # Lines 5, 6, 12: "Connection pool exhausted"
        r5, r6, r12 = results[4], results[5], results[11]
        self.assertEqual(r5.event_id, r6.event_id)
        self.assertEqual(r6.event_id, r12.event_id)
        self.assertEqual(r5.group_id, r6.group_id)
        self.assertEqual(r6.group_id, r12.group_id)
        self.assertEqual(r5.event_template, "Connection pool exhausted")

        # Lines 7, 8: "Failed to execute database query"
        r7, r8 = results[6], results[7]
        self.assertEqual(r7.event_id, r8.event_id)
        self.assertEqual(r7.group_id, r8.group_id)

        # Lines 9, 10: "Database retry attempt <NUM>"
        r9, r10 = results[8], results[9]
        self.assertEqual(r9.event_id, r10.event_id)
        self.assertEqual(r9.group_id, r10.group_id)
        self.assertEqual(r9.event_template, "Database retry attempt <NUM>")

    def test_explicit_hdfs_block_preserved(self):
        """Verify that explicit HDFS block IDs (blk_-?\\d+) are preserved when present."""
        hdfs_line = "081109 203615 148 INFO dfs.DataNode: Receiving block blk_-1608999687919862906 from /10.0.0.1"
        res = self.parser.parse(hdfs_line)
        self.assertEqual(res.block_ids, ["blk_-1608999687919862906"])
        self.assertEqual(res.block_id, "blk_-1608999687919862906")
        self.assertEqual(res.group_id, "blk_-1608999687919862906")


class TestFeatureExtractorBlockGrouping(unittest.TestCase):
    """Unit tests for BlockFeatureExtractor grouping behavior."""

    def test_group_events_by_block_produces_non_zero_blocks(self):
        """Verify group_events_by_block creates valid groups for all generic application events."""
        parser = DrainParser()
        results = parser.parse_lines(SAMPLE_APP_LOGS, update_model=True)
        event_dicts = [r.to_dict() for r in results]

        groups = BlockFeatureExtractor.group_events_by_block(event_dicts)
        self.assertEqual(len(groups), 6)

        # Confirm total events across all blocks equals 12
        total_grouped_events = sum(len(evs) for evs in groups.values())
        self.assertEqual(total_grouped_events, 12)

        # Confirm cluster for connection timeouts has 3 events
        timeout_group = results[2].group_id
        self.assertEqual(len(groups[timeout_group]), 3)

        # Confirm cluster for pool exhausted has 3 events
        pool_group = results[4].group_id
        self.assertEqual(len(groups[pool_group]), 3)

        # Confirm cluster for failed queries has 2 events
        query_group = results[6].group_id
        self.assertEqual(len(groups[query_group]), 2)

        # Confirm cluster for retry attempts has 2 events
        retry_group = results[8].group_id
        self.assertEqual(len(groups[retry_group]), 2)


class TestPipelineEndToEndRegression(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration test for PipelineService.analyze_logs."""

    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.pipeline = PipelineService()

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_exact_sample_with_threshold_zero(self):
        """Verify exact user input with session_id='logsage-exact-regression-001' and threshold=0."""
        async with self.SessionLocal() as session:
            resp = await self.pipeline.analyze_logs(
                SAMPLE_APP_LOGS,
                session_id="logsage-exact-regression-001",
                db=session,
                threshold=0.0,
            )

            # Response schema verification
            self.assertEqual(resp.total_lines, 12)
            self.assertEqual(resp.total_blocks, 6)
            self.assertEqual(resp.anomalous_blocks, 6)
            self.assertEqual(resp.incidents_created, 6)
            self.assertEqual(len(resp.incidents), 6)

            # Database persistence verification
            entry_res = await session.execute(
                select(LogEntry).where(LogEntry.session_id == "logsage-exact-regression-001")
            )
            entries = entry_res.scalars().all()
            self.assertEqual(len(entries), 12)

            for entry in entries:
                # LogEntry accurately preserves block_id=None for non-HDFS logs
                self.assertIsNone(entry.block_id)
                self.assertIsNotNone(entry.level)
                self.assertIsNotNone(entry.event_template)

            # Incidents verification
            inc_res = await session.execute(select(Incident))
            incidents = inc_res.scalars().all()
            self.assertEqual(len(incidents), 6)

            for inc in incidents:
                self.assertTrue(inc.incident_id.startswith("INC-"))
                self.assertTrue(inc.block_id.startswith("cluster_E"))
                self.assertGreaterEqual(inc.anomaly_score, 0.0)
                self.assertLessEqual(inc.anomaly_score, 1.0)
                evidence = json.loads(inc.raw_evidence_json)
                self.assertTrue(len(evidence) > 0)
                # Verify evidence contains original log lines
                self.assertIn("2026-11-19 10:00:", evidence[0])

    async def test_sample_with_default_threshold(self):
        """Verify that at default threshold 0.5, benign INFO lines are not flagged as anomalous."""
        async with self.SessionLocal() as session:
            resp = await self.pipeline.analyze_logs(
                SAMPLE_APP_LOGS,
                session_id="logsage-default-threshold",
                db=session,
                threshold=0.5,
            )

            self.assertEqual(resp.total_lines, 12)
            self.assertEqual(resp.total_blocks, 6)
            # 4 anomalous blocks (2x connection issues, 1x query fail, 1x retries)
            self.assertEqual(resp.anomalous_blocks, 4)
            self.assertEqual(resp.incidents_created, 4)

            # Severities
            inc_map = {inc.block_id: inc.severity for inc in resp.incidents}
            self.assertIn(inc_map["cluster_E3"], ("CRITICAL", "HIGH"))
            self.assertIn(inc_map["cluster_E4"], ("CRITICAL", "HIGH"))
            self.assertEqual(inc_map["cluster_E5"], "HIGH")
            self.assertEqual(inc_map["cluster_E6"], "MEDIUM")


if __name__ == "__main__":
    unittest.main()
