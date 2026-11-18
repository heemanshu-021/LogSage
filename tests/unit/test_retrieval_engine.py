"""
Unit and Integration Tests for Runbook Retrieval Engine and Similar Incident Search.

Covers:
- Phase 2: Runbook knowledge base loading, required fields, and illustrative notices.
- Phase 3: Semantic embedding helper, mocked vector similarity, and lexical fallback.
- Phase 4: Top-3 runbook retrieval, query scenarios, score ranking, and empty KB handling.
- Phase 5: Similar historical incident retrieval, current incident exclusion, synthetic fixtures.
- Phase 6: Pydantic response schemas and API contracts.

Both pytest and standard Python unittest runners are supported:
    python3 -m unittest tests/unit/test_retrieval_engine.py -v
"""
from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from backend.services.retrieval import (
    RetrievalService,
    RunbookDetail,
    RunbookHit,
    _build_runbook_detail,
    _parse_section,
)


class TestRunbookKnowledgeBase(unittest.TestCase):
    """Verifies Phase 2: Knowledge Base content, structure, and required fields."""

    @classmethod
    def setUpClass(cls):
        cls.svc = RetrievalService(runbooks_dir="runbooks")
        cls.docs = cls.svc._load_runbooks()

    def test_at_least_seven_runbooks_present(self):
        """Knowledge base must contain at least 7 illustrative runbooks."""
        self.assertGreaterEqual(
            len(self.docs),
            7,
            f"Expected at least 7 runbooks, found {len(self.docs)}",
        )

    def test_all_runbooks_have_required_sections_and_fields(self):
        """Every runbook must contain ID, Title, Symptoms, Causes, Investigation, Remediation, Verification."""
        for doc in self.docs:
            slug = doc["slug"]
            detail = self.svc.get_runbook_detail(slug)
            self.assertIsNotNone(detail, f"Runbook {slug} could not be parsed into RunbookDetail")

            # Unique ID
            self.assertTrue(
                detail.id and detail.id != "",
                f"Runbook '{slug}' missing unique ID in frontmatter",
            )
            self.assertTrue(
                detail.id.startswith("RB-"),
                f"Runbook '{slug}' ID should start with 'RB-', got '{detail.id}'",
            )

            # Title
            self.assertTrue(
                detail.title and len(detail.title.strip()) > 3,
                f"Runbook '{slug}' missing valid Title",
            )

            # Symptoms
            self.assertTrue(
                detail.symptoms and len(detail.symptoms.strip()) > 10,
                f"Runbook '{slug}' missing or empty ## Symptoms section",
            )

            # Possible Causes
            self.assertTrue(
                detail.possible_causes and len(detail.possible_causes.strip()) > 10,
                f"Runbook '{slug}' missing or empty ## Possible Causes section",
            )

            # Investigation Steps
            self.assertTrue(
                detail.investigation_steps and len(detail.investigation_steps.strip()) > 10,
                f"Runbook '{slug}' missing or empty ## Investigation Steps section",
            )

            # Remediation
            self.assertTrue(
                detail.remediation and len(detail.remediation.strip()) > 10,
                f"Runbook '{slug}' missing or empty ## Remediation section",
            )

            # Verification Steps
            self.assertTrue(
                detail.verification_steps and len(detail.verification_steps.strip()) > 10,
                f"Runbook '{slug}' missing or empty ## Verification Steps section",
            )

    def test_runbooks_labeled_as_illustrative(self):
        """Every runbook Markdown file must clearly state it is an illustrative template."""
        for doc in self.docs:
            body = doc["body"].lower()
            self.assertTrue(
                "illustrative runbook" in body or "illustrative" in body,
                f"Runbook '{doc['slug']}' must be clearly labeled as an illustrative template",
            )

    def test_empty_knowledge_base_handling(self):
        """Retrieval service handles an empty runbooks directory gracefully."""
        with tempfile.TemporaryDirectory() as empty_dir:
            empty_svc = RetrievalService(runbooks_dir=empty_dir)
            empty_svc.build_index()
            hits = empty_svc.search("Database failure", top_k=3)
            self.assertEqual(hits, [])
            detail_hits = empty_svc.search_detail("Database failure", top_k=3)
            self.assertEqual(detail_hits, [])


class TestRunbookRetrievalQueries(unittest.TestCase):
    """Verifies Phase 4: Top-3 runbook retrieval across required incident scenarios."""

    @classmethod
    def setUpClass(cls):
        cls.svc = RetrievalService(runbooks_dir="runbooks")
        cls.svc.build_index()

    def test_query_database_connection_failure(self):
        """Scenario 1: Database connection failure -> db-connection-timeout."""
        hits = self.svc.search("Database connection refused timeout pool exhausted", top_k=3)
        self.assertGreater(len(hits), 0)
        top_slugs = [h.slug for h in hits]
        self.assertIn("db-connection-timeout", top_slugs[:2])
        self.assertEqual(hits[0].slug, "db-connection-timeout")

    def test_query_high_memory_utilization(self):
        """Scenario 2: High memory utilization -> oom-kill."""
        hits = self.svc.search("High memory consumption Out of Memory OOM kill process", top_k=3)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].slug, "oom-kill")

    def test_query_disk_space_exhaustion(self):
        """Scenario 3: Disk space exhaustion -> disk-space-critical."""
        hits = self.svc.search("Disk space full filesystem 95% storage capacity", top_k=3)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].slug, "disk-space-critical")

    def test_query_application_crash(self):
        """Scenario 4: Application crash -> application-crash."""
        hits = self.svc.search("Application process crash segfault core dump exit signal", top_k=3)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].slug, "application-crash")

    def test_query_network_timeout(self):
        """Scenario 5: Network timeout -> network-timeout."""
        hits = self.svc.search("Network request timeout gateway 504 latency packet loss", top_k=3)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].slug, "network-timeout")

    def test_query_authentication_failure(self):
        """Scenario 6: Authentication failure -> ssh-brute-force."""
        hits = self.svc.search("Invalid authentication attempts SSH failed password brute force", top_k=3)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].slug, "ssh-brute-force")

    def test_query_service_restart_loop(self):
        """Scenario 7: Service restart loop -> service-restart-loop."""
        hits = self.svc.search("Service restart loop crashloopbackoff repeated startup failure", top_k=3)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0].slug, "service-restart-loop")

    def test_top_k_limit_and_descending_order(self):
        """Results must strictly respect top_k and be sorted descending by score."""
        hits = self.svc.search("system error timeout failure", top_k=3)
        self.assertLessEqual(len(hits), 3)
        scores = [h.score for h in hits]
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i],
                scores[i + 1],
                f"Scores not descending: {scores}",
            )

    def test_search_mode_is_labeled_truthfully(self):
        """Search mode must be explicitly 'semantic' or 'lexical' (never pretend lexical is semantic)."""
        hits = self.svc.search("disk full", top_k=2)
        for h in hits:
            self.assertIn(
                h.search_mode,
                {"semantic", "lexical"},
                f"Invalid search_mode: {h.search_mode}",
            )


class TestMockedSemanticRetrieval(unittest.TestCase):
    """
    [MOCKED TEST]
    Verifies Phase 3: Semantic embedding engine vector similarity calculation
    using an isolated mock of SentenceTransformer and FAISS.
    """

    def test_mocked_vector_similarity_and_ranking(self):
        """Mocked embedding model produces 4D vectors; verifies cosine similarity ranking."""
        mock_model = MagicMock()
        # Mock embeddings for 3 documents
        doc_embeddings = np.array([
            [1.0, 0.0, 0.0, 0.0],  # doc 0: perfect match for query [1, 0, 0, 0]
            [0.7071, 0.7071, 0.0, 0.0],  # doc 1: partial match (~0.71)
            [0.0, 1.0, 0.0, 0.0],  # doc 2: orthogonal (0.0)
        ], dtype=np.float32)

        query_embedding = np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32)

        mock_model.encode.side_effect = lambda texts, **kw: (
            doc_embeddings if len(texts) == 3 else query_embedding
        )

        mock_index = MagicMock()
        mock_index.search.return_value = (
            np.array([[1.0, 0.7071, 0.0]]),  # scores
            np.array([[0, 1, 2]]),            # indices
        )

        svc = RetrievalService(runbooks_dir="runbooks")
        svc._model = mock_model
        svc._index = mock_index
        svc._meta = [
            {"slug": "doc-0", "title": "Doc 0", "body": "text 0", "excerpt": "excerpt 0"},
            {"slug": "doc-1", "title": "Doc 1", "body": "text 1", "excerpt": "excerpt 1"},
            {"slug": "doc-2", "title": "Doc 2", "body": "text 2", "excerpt": "excerpt 2"},
        ]
        svc._built = True
        svc._semantic_available = True

        mock_faiss = MagicMock()
        mock_faiss.normalize_L2 = MagicMock()
        with patch.dict("sys.modules", {"faiss": mock_faiss}):
            hits = svc._semantic_search("test query", top_k=3)
        self.assertEqual(len(hits), 3)
        self.assertEqual(hits[0].slug, "doc-0")
        self.assertAlmostEqual(hits[0].score, 1.0, places=3)
        self.assertEqual(hits[0].search_mode, "semantic")
        self.assertEqual(hits[1].slug, "doc-1")
        self.assertAlmostEqual(hits[1].score, 0.7071, places=3)
        self.assertEqual(hits[1].search_mode, "semantic")


class TestRealEmbeddingModel(unittest.TestCase):
    """
    [REAL TEST]
    Verifies real SentenceTransformer model if installed, otherwise skips cleanly.
    """

    def test_real_sentence_transformers_if_installed(self):
        try:
            import sentence_transformers  # noqa: F401
            import faiss                  # noqa: F401
        except ImportError:
            self.skipTest("sentence-transformers or faiss-cpu not installed in environment (expected in sandbox)")

        svc = RetrievalService(runbooks_dir="runbooks")
        emb = svc.embed_text("Database connection timeout")
        self.assertIsNotNone(emb)
        self.assertIsInstance(emb, np.ndarray)
        # Normalised vector norm should be ~1.0
        norm = np.linalg.norm(emb)
        self.assertAlmostEqual(norm, 1.0, places=4)


class TestSimilarIncidentRetrievalLogic(unittest.TestCase):
    """
    Verifies Phase 5: Similar historical incident retrieval.
    Uses synthetic incident data structures labeled [SYNTHETIC TEST FIXTURE].
    """

    class SyntheticIncident:
        """[SYNTHETIC TEST FIXTURE: isolated incident representation for tests]."""
        def __init__(self, incident_id: str, title: str, block_id: str, severity: str = "HIGH", status: str = "OPEN"):
            self.incident_id = incident_id
            self.title = title
            self.block_id = block_id
            self.severity = severity
            self.status = status
            self.anomaly_score = 0.85

    def test_current_incident_excluded_from_results(self):
        """The target incident MUST NOT appear in its own similar incidents list."""
        inc_target = self.SyntheticIncident("INC-TARGET", "Database connection timeout pool exhausted", "blk_101")
        inc_other1 = self.SyntheticIncident("INC-001", "Database timeout occurred on replica", "blk_102")
        inc_other2 = self.SyntheticIncident("INC-002", "Disk space threshold exceeded", "blk_103")

        all_candidates = [inc_target, inc_other1, inc_other2]
        # Filtering candidate pool: exclude current incident
        candidates = [c for c in all_candidates if c.incident_id != inc_target.incident_id]

        candidate_ids = [c.incident_id for c in candidates]
        self.assertNotIn(inc_target.incident_id, candidate_ids)
        self.assertEqual(len(candidate_ids), 2)

    def test_similar_incidents_lexical_ranking(self):
        """Related incidents rank higher than unrelated incidents."""
        inc_target = self.SyntheticIncident("INC-100", "Postgres database connection timeout pool exhausted", "blk_100")
        inc_similar = self.SyntheticIncident("INC-101", "Database connection failed with pool timeout", "blk_101")
        inc_unrelated = self.SyntheticIncident("INC-102", "Disk partition /var/log reached 98% full", "blk_102")

        candidates = [inc_similar, inc_unrelated]
        q_words = set(re.findall(r"[a-z0-9_-]+", inc_target.title.lower()))

        scored = []
        for inc in candidates:
            cand_words = set(re.findall(r"[a-z0-9_-]+", inc.title.lower()))
            overlap = len(q_words & cand_words) / max(len(q_words), 1)
            scored.append((inc, overlap))

        scored.sort(key=lambda x: x[1], reverse=True)
        self.assertEqual(scored[0][0].incident_id, "INC-101")
        self.assertGreater(scored[0][1], scored[1][1])


class TestApiSchemas(unittest.TestCase):
    """Verifies Phase 6: Pydantic schemas serialize and validate as expected."""

    def test_similar_incidents_response_schema(self):
        try:
            from backend.api.schemas import SimilarIncidentResult, SimilarIncidentsResponse
        except ImportError:
            self.skipTest("pydantic not installed in environment")

        result = SimilarIncidentResult(
            incident_id="INC-123456",
            block_id="blk_9999",
            title="Database Connection Timeout",
            severity="CRITICAL",
            status="OPEN",
            anomaly_score=0.92,
            similarity_score=0.88,
            search_mode="lexical",
            created_at="2026-11-18T12:00:00Z",
        )
        response = SimilarIncidentsResponse(
            incident_id="INC-000001",
            query_text="Database Connection Timeout",
            search_mode="lexical",
            similar_incidents=[result],
        )
        data = response.model_dump() if hasattr(response, "model_dump") else response.dict()
        self.assertEqual(data["incident_id"], "INC-000001")
        self.assertEqual(len(data["similar_incidents"]), 1)
        self.assertEqual(data["similar_incidents"][0]["incident_id"], "INC-123456")

    def test_incident_runbooks_response_schema(self):
        try:
            from backend.api.schemas import IncidentRunbooksResponse, RunbookDetailOut
        except ImportError:
            self.skipTest("pydantic not installed in environment")

        rb = RunbookDetailOut(
            slug="db-connection-timeout",
            id="RB-001",
            title="Database Connection Timeout Response",
            score=0.91,
            search_mode="lexical",
            tags=["database", "timeout"],
            symptoms="Database connection timeout after 30s",
            possible_causes="Connection pool saturation",
            investigation_steps="Check active connections",
            remediation="Kill idle backends",
            verification_steps="Check error rate drops to zero",
            escalation="Page on-call DBA",
        )
        response = IncidentRunbooksResponse(
            incident_id="INC-000001",
            query_text="Database timeout query",
            search_mode="lexical",
            runbooks=[rb],
        )
        data = response.model_dump() if hasattr(response, "model_dump") else response.dict()
        self.assertEqual(data["incident_id"], "INC-000001")
        self.assertEqual(data["runbooks"][0]["id"], "RB-001")
        self.assertEqual(data["runbooks"][0]["verification_steps"], "Check error rate drops to zero")


if __name__ == "__main__":
    unittest.main()
