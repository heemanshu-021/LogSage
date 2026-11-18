"""
Backend API integration tests using a subprocess uvicorn server.

Starts the real uvicorn server in a background subprocess,
waits for it to be ready, then tests all endpoints with httpx.
No async needed — all httpx calls are synchronous.
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import time

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8765"
STARTUP_TIMEOUT = 15  # seconds to wait for server ready


SAMPLE_LINES = [
    "081109 203615 148 INFO dfs.DataNode: Receiving block blk_100 from /10.0.0.1",
    "081109 203616 148 INFO dfs.DataNode: Receiving block blk_101 from /10.0.0.2",
    "081109 203617 148 ERROR dfs.DataNode: IOException in DataXceiver for block blk_999",
    "081109 203618 35  ERROR dfs.FSNamesystem: BLOCK NameSystem markBlockAsCorrupt blk_999",
    "081109 203619 148 INFO dfs.DataNode: Receiving block blk_102 from /10.0.0.3",
    "081109 203620 148 INFO dfs.DataNode: Receiving block blk_103 from /10.0.0.4",
    "081109 203621 148 INFO dfs.DataNode: Receiving block blk_104 from /10.0.0.5",
    "081109 203622 148 INFO dfs.DataNode: Receiving block blk_105 from /10.0.0.6",
    "081109 203623 35  WARN dfs.DataNode: Slow I/O for block blk_200",
    "081109 203624 148 INFO dfs.DataNode: Receiving block blk_106 from /10.0.0.7",
    "081109 203625 148 INFO dfs.DataNode: Receiving block blk_107 from /10.0.0.8",
    "081109 203626 148 INFO dfs.DataNode: Receiving block blk_108 from /10.0.0.9",
]


# ---------------------------------------------------------------------------
# Server lifecycle fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def server():
    """
    Launch uvicorn in a subprocess, wait for /health to respond,
    yield the base URL, then terminate the subprocess.
    """
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test_logsage.db"

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", "127.0.0.1",
            "--port", "8765",
            "--log-level", "warning",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    # Wait for the server to become ready
    deadline = time.time() + STARTUP_TIMEOUT
    while time.time() < deadline:
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=1.0)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.fail("Server did not start within timeout")

    yield BASE_URL

    proc.terminate()
    proc.wait(timeout=5)
    # Clean up test DB
    test_db = "data/test_logsage.db"
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture(scope="session")
def client(server):
    with httpx.Client(base_url=server, timeout=10.0) as c:
        yield c


# ===========================================================================
# GET /health  &  GET /api/health
# ===========================================================================

class TestHealth:
    def test_health_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_schema(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert "timestamp" in data
        assert data["database"] == "ok"
        assert data["version"] == "0.1.0"
        assert isinstance(data["ml_model_loaded"], bool)

    def test_api_health_same_as_root(self, client):
        r1 = client.get("/health")
        r2 = client.get("/api/health")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["status"] == r2.json()["status"] == "ok"


# ===========================================================================
# POST /api/logs/upload
# ===========================================================================

class TestLogUpload:
    @staticmethod
    def _make_file(content: str, filename: str):
        return ("file", (filename, io.BytesIO(content.encode()), "text/plain"))

    def test_upload_valid_log(self, client):
        content = "\n".join(SAMPLE_LINES)
        resp = client.post(
            "/api/logs/upload",
            files=[self._make_file(content, "test_hdfs.log")],
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "file_id" in data
        assert data["total_lines"] == len(SAMPLE_LINES)
        assert data["filename"] == "test_hdfs.log"

    def test_upload_txt_extension(self, client):
        resp = client.post(
            "/api/logs/upload",
            files=[self._make_file("line1\nline2", "test.txt")],
        )
        assert resp.status_code == 201

    def test_upload_csv_extension(self, client):
        resp = client.post(
            "/api/logs/upload",
            files=[self._make_file("a,b,c\n1,2,3", "data.csv")],
        )
        assert resp.status_code == 201

    def test_upload_rejected_bad_extension(self, client):
        resp = client.post(
            "/api/logs/upload",
            files=[self._make_file("binary data", "malware.exe")],
        )
        assert resp.status_code == 400
        assert "Unsupported file format" in resp.json()["detail"]

    def test_upload_rejected_oversized(self, client):
        big_content = "A" * (26 * 1024 * 1024)
        resp = client.post(
            "/api/logs/upload",
            files=[self._make_file(big_content, "big.log")],
        )
        assert resp.status_code == 413

    def test_upload_response_has_size_bytes(self, client):
        content = "line one\nline two\n"
        resp = client.post(
            "/api/logs/upload",
            files=[self._make_file(content, "s.log")],
        )
        assert resp.status_code == 201
        assert resp.json()["size_bytes"] == len(content.encode())


# ===========================================================================
# POST /api/logs/analyze
# ===========================================================================

class TestLogAnalyze:
    def test_analyze_returns_200(self, client):
        resp = client.post("/api/logs/analyze", json={"lines": SAMPLE_LINES})
        assert resp.status_code == 200

    def test_analyze_response_schema(self, client):
        resp = client.post("/api/logs/analyze", json={"lines": SAMPLE_LINES})
        data = resp.json()
        # Fields from actual AnalyzeResponse schema
        required = {
            "session_id", "total_lines", "total_blocks",
            "anomalous_blocks", "incidents_created", "processing_time_ms",
        }
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_analyze_counts_non_negative(self, client):
        resp = client.post("/api/logs/analyze", json={"lines": SAMPLE_LINES})
        data = resp.json()
        assert data["total_lines"] >= 0
        assert data["total_blocks"] >= 0
        assert data["anomalous_blocks"] >= 0
        assert data["incidents_created"] >= 0

    def test_analyze_empty_lines_rejected(self, client):
        resp = client.post("/api/logs/analyze", json={"lines": []})
        assert resp.status_code == 422

    def test_analyze_no_body_rejected(self, client):
        resp = client.post("/api/logs/analyze", json={})
        assert resp.status_code == 422

    def test_analyze_incidents_field_is_list(self, client):
        resp = client.post("/api/logs/analyze", json={"lines": SAMPLE_LINES})
        assert isinstance(resp.json().get("incidents", []), list)

    def test_analyze_ml_model_loaded(self, client):
        """If ML model is loaded, anomaly detection pipeline must run."""
        health = client.get("/health").json()
        if not health["ml_model_loaded"]:
            pytest.skip("ML model not loaded — skipping anomaly detection test")
        resp = client.post("/api/logs/analyze", json={"lines": SAMPLE_LINES})
        assert resp.status_code == 200


# ===========================================================================
# GET /api/incidents
# ===========================================================================

class TestIncidentList:
    @pytest.fixture(autouse=True)
    def seed(self, client):
        """Seed DB with at least one analyze call."""
        client.post("/api/logs/analyze", json={"lines": SAMPLE_LINES})

    def test_list_200(self, client):
        assert client.get("/api/incidents").status_code == 200

    def test_list_schema(self, client):
        data = client.get("/api/incidents").json()
        for f in ("total", "incidents", "limit", "offset"):
            assert f in data

    def test_pagination(self, client):
        data = client.get("/api/incidents?limit=5&offset=0").json()
        assert len(data["incidents"]) <= 5

    def test_severity_filter(self, client):
        for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            resp = client.get(f"/api/incidents?severity={sev}")
            assert resp.status_code == 200
            for inc in resp.json()["incidents"]:
                assert inc["severity"] == sev

    def test_status_filter(self, client):
        resp = client.get("/api/incidents?status=OPEN")
        assert resp.status_code == 200
        for inc in resp.json()["incidents"]:
            assert inc["status"] == "OPEN"

    def test_incident_summary_fields(self, client):
        data = client.get("/api/incidents").json()
        for inc in data["incidents"]:
            for f in ("incident_id", "block_id", "title", "severity",
                      "status", "anomaly_score", "event_count", "created_at"):
                assert f in inc, f"Missing: {f}"


# ===========================================================================
# GET /api/incidents/{incident_id}
# ===========================================================================

class TestIncidentDetail:
    def test_404_for_unknown(self, client):
        resp = client.get("/api/incidents/INC-DOESNOTEXIST999")
        assert resp.status_code == 404

    def test_detail_schema_if_exists(self, client):
        client.post("/api/logs/analyze", json={"lines": SAMPLE_LINES})
        list_data = client.get("/api/incidents?limit=1").json()
        if list_data["total"] == 0:
            pytest.skip("No incidents in DB — skipping detail schema test")
        inc_id = list_data["incidents"][0]["incident_id"]
        resp = client.get(f"/api/incidents/{inc_id}")
        assert resp.status_code == 200
        data = resp.json()
        for f in ("incident_id", "block_id", "title", "severity", "status",
                  "anomaly_score", "top_features", "raw_evidence",
                  "recommended_runbooks", "created_at"):
            assert f in data, f"Missing: {f}"

    def test_raw_evidence_is_list(self, client):
        list_data = client.get("/api/incidents?limit=1").json()
        if list_data["total"] == 0:
            pytest.skip("No incidents")
        inc_id = list_data["incidents"][0]["incident_id"]
        data = client.get(f"/api/incidents/{inc_id}").json()
        assert isinstance(data["raw_evidence"], list)

    def test_recommended_runbooks_is_list(self, client):
        list_data = client.get("/api/incidents?limit=1").json()
        if list_data["total"] == 0:
            pytest.skip("No incidents")
        inc_id = list_data["incidents"][0]["incident_id"]
        data = client.get(f"/api/incidents/{inc_id}").json()
        assert isinstance(data["recommended_runbooks"], list)


# ===========================================================================
# GET /api/dashboard/metrics
# ===========================================================================

class TestDashboard:
    def test_metrics_200(self, client):
        assert client.get("/api/dashboard/metrics").status_code == 200

    def test_metrics_schema(self, client):
        data = client.get("/api/dashboard/metrics").json()
        # Fields from actual DashboardMetrics schema
        for f in ("total_logs_ingested", "total_blocks_analyzed", "total_incidents",
                  "open_incidents", "severity_breakdown", "status_breakdown"):
            assert f in data, f"Missing: {f}"

    def test_metrics_non_negative(self, client):
        data = client.get("/api/dashboard/metrics").json()
        assert data["total_logs_ingested"] >= 0
        assert data["total_blocks_analyzed"] >= 0
        assert data["total_incidents"] >= 0
        assert data["open_incidents"] >= 0

    def test_severity_breakdown_is_dict(self, client):
        assert isinstance(client.get("/api/dashboard/metrics").json()["severity_breakdown"], dict)

    def test_status_breakdown_is_dict(self, client):
        assert isinstance(client.get("/api/dashboard/metrics").json()["status_breakdown"], dict)
