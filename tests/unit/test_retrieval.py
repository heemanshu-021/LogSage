"""Unit tests for the runbook retrieval service."""
from __future__ import annotations

import pytest

from backend.services.retrieval import RetrievalService


@pytest.fixture
def svc():
    s = RetrievalService(runbooks_dir="runbooks")
    s.build_index()
    return s


def test_index_builds(svc):
    assert svc._built
    assert len(svc._meta) >= 5


def test_search_returns_hits(svc):
    hits = svc.search("HDFS block corruption", top_k=3)
    assert len(hits) > 0
    assert all(0.0 <= h.score <= 1.0 for h in hits)


def test_search_top_k_respected(svc):
    hits = svc.search("memory out of memory kill process", top_k=2)
    assert len(hits) <= 2


def test_search_oom_ranks_oom_runbook_first(svc):
    hits = svc.search("Out of memory OOM kill process kernel", top_k=5)
    slugs = [h.slug for h in hits]
    assert "oom-kill" in slugs, f"Expected oom-kill in top results, got: {slugs}"


def test_search_ssh_brute_force(svc):
    hits = svc.search("Failed password invalid user SSH brute force", top_k=3)
    slugs = [h.slug for h in hits]
    assert "ssh-brute-force" in slugs


def test_search_db_timeout(svc):
    hits = svc.search("database connection timeout retries", top_k=3)
    slugs = [h.slug for h in hits]
    assert "db-connection-timeout" in slugs


def test_excerpt_is_non_empty(svc):
    hits = svc.search("disk space full critical", top_k=1)
    assert hits[0].excerpt.strip() != ""
