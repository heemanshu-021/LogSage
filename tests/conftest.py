"""Shared pytest fixtures."""
import os
import pytest

# Always use in-memory DB for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
