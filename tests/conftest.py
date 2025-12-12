"""Pytest fixtures for jueehanbeoneun tests."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime


@pytest.fixture
def sample_questions():
    """Sample questions for testing."""
    return [
        {"id": 1, "text": "Test question 1", "category": "past", "difficulty": 1},
        {"id": 2, "text": "Test question 2", "category": "present", "difficulty": 2},
        {"id": 3, "text": "Test question 3", "category": "future", "difficulty": 3},
    ]


@pytest.fixture
def temp_questions_file(sample_questions):
    """Create a temporary questions JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump({"questions": sample_questions}, f, ensure_ascii=False)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_subscribers_file():
    """Create a temporary subscribers JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump({"subscribers": [], "sent_log": []}, f, ensure_ascii=False)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def fixed_date():
    """Fixed date for deterministic testing."""
    return datetime(2024, 12, 12, 9, 0, 0)
