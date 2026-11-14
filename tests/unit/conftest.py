"""
Shared pytest fixtures.
"""
import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
