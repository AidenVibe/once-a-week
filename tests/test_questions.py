"""Tests for question loading and selection logic."""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "bot"))


class TestGetQuestionForDate:
    """Tests for get_question_for_date function."""

    def test_same_date_returns_same_question(self, sample_questions):
        """Same date should always return the same question."""
        from main import get_question_for_date

        date = datetime(2024, 12, 12)
        q1 = get_question_for_date(sample_questions, date)
        q2 = get_question_for_date(sample_questions, date)

        assert q1["id"] == q2["id"]

    def test_different_dates_cycle_through_questions(self, sample_questions):
        """Questions should cycle through based on date."""
        from main import get_question_for_date

        start_date = datetime(2024, 12, 12)
        results = []

        for i in range(len(sample_questions) * 2):
            date = start_date + timedelta(days=i)
            q = get_question_for_date(sample_questions, date)
            results.append(q["id"])

        # First cycle
        assert results[0] == 1
        assert results[1] == 2
        assert results[2] == 3

        # Second cycle (repeats)
        assert results[3] == 1
        assert results[4] == 2
        assert results[5] == 3

    def test_empty_questions_returns_none(self):
        """Empty question list should return None."""
        from main import get_question_for_date

        result = get_question_for_date([], datetime.now())
        assert result is None

    def test_negative_date_difference(self, sample_questions):
        """Dates before start date should still work."""
        from main import get_question_for_date

        # One day before start date
        date = datetime(2024, 12, 11)
        q = get_question_for_date(sample_questions, date)

        assert q is not None
        assert q["id"] in [1, 2, 3]


class TestGetWeekQuestions:
    """Tests for get_week_questions function."""

    def test_returns_seven_items(self, sample_questions, monkeypatch):
        """Should return exactly 7 items for the week."""
        from main import get_week_questions

        # Mock datetime to a known date
        class MockDatetime:
            @classmethod
            def now(cls):
                return datetime(2024, 12, 12, 10, 0, 0)

        monkeypatch.setattr("main.datetime", MockDatetime)

        # Need to patch load_questions too
        import main
        original_load = main.load_questions
        main.load_questions = lambda: sample_questions

        try:
            week = get_week_questions(sample_questions)
            assert len(week) == 7
        finally:
            main.load_questions = original_load

    def test_today_is_marked(self, sample_questions):
        """Current day should be marked as today."""
        from main import get_week_questions

        week = get_week_questions(sample_questions)

        # Exactly one day should be marked as today
        today_count = sum(1 for item in week if item["is_today"])
        assert today_count == 1


class TestGetRandomQuestion:
    """Tests for get_random_question function."""

    def test_excludes_specified_question(self, sample_questions):
        """Should not return the excluded question."""
        from main import get_random_question

        # Exclude question 1, run multiple times
        for _ in range(20):
            q = get_random_question(sample_questions, exclude_id=1)
            assert q["id"] != 1

    def test_returns_question_when_no_exclusion(self, sample_questions):
        """Should return a valid question without exclusion."""
        from main import get_random_question

        q = get_random_question(sample_questions)
        assert q is not None
        assert q["id"] in [1, 2, 3]

    def test_empty_questions_returns_none(self):
        """Empty question list should return None."""
        from main import get_random_question

        result = get_random_question([])
        assert result is None


class TestLoadQuestions:
    """Tests for load_questions function."""

    def test_loads_valid_json(self, temp_questions_file, monkeypatch):
        """Should load questions from valid JSON file."""
        import main

        # Patch the QUESTIONS_PATH
        monkeypatch.setattr(main, "QUESTIONS_PATH", temp_questions_file)

        questions = main.load_questions()

        assert len(questions) == 3
        assert questions[0]["id"] == 1

    def test_handles_missing_file(self, monkeypatch):
        """Should return empty list for missing file."""
        import main
        from pathlib import Path

        monkeypatch.setattr(main, "QUESTIONS_PATH", Path("/nonexistent/path.json"))

        questions = main.load_questions()
        assert questions == []

    def test_handles_invalid_json(self, monkeypatch, tmp_path):
        """Should return empty list for invalid JSON."""
        import main

        # Create file with invalid JSON
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }", encoding="utf-8")

        monkeypatch.setattr(main, "QUESTIONS_PATH", invalid_file)

        questions = main.load_questions()
        assert questions == []
