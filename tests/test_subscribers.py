"""Tests for subscriber management logic."""

import pytest
import json
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "bot"))


class TestAddSubscriber:
    """Tests for add_subscriber function."""

    def test_adds_new_subscriber(self, temp_subscribers_file, monkeypatch):
        """Should add a new subscriber and return True."""
        import main

        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", temp_subscribers_file)
        monkeypatch.setattr(main, "DATA_DIR", temp_subscribers_file.parent)

        result = main.add_subscriber(12345, "testuser")

        assert result is True

        # Verify subscriber was saved
        with open(temp_subscribers_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["subscribers"]) == 1
        assert data["subscribers"][0]["chat_id"] == 12345
        assert data["subscribers"][0]["username"] == "testuser"

    def test_returns_false_for_existing_subscriber(self, temp_subscribers_file, monkeypatch):
        """Should return False for duplicate subscriber."""
        import main

        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", temp_subscribers_file)
        monkeypatch.setattr(main, "DATA_DIR", temp_subscribers_file.parent)

        # Add subscriber first time
        result1 = main.add_subscriber(12345, "testuser")
        assert result1 is True

        # Try to add same subscriber again
        result2 = main.add_subscriber(12345, "testuser")
        assert result2 is False

        # Verify only one subscriber exists
        with open(temp_subscribers_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["subscribers"]) == 1

    def test_multiple_unique_subscribers(self, temp_subscribers_file, monkeypatch):
        """Should add multiple unique subscribers."""
        import main

        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", temp_subscribers_file)
        monkeypatch.setattr(main, "DATA_DIR", temp_subscribers_file.parent)

        main.add_subscriber(111, "user1")
        main.add_subscriber(222, "user2")
        main.add_subscriber(333, "user3")

        with open(temp_subscribers_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["subscribers"]) == 3


class TestRemoveSubscriber:
    """Tests for remove_subscriber function."""

    def test_removes_existing_subscriber(self, temp_subscribers_file, monkeypatch):
        """Should remove existing subscriber and return True."""
        import main

        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", temp_subscribers_file)
        monkeypatch.setattr(main, "DATA_DIR", temp_subscribers_file.parent)

        # Add subscriber first
        main.add_subscriber(12345, "testuser")

        # Remove subscriber
        result = main.remove_subscriber(12345)

        assert result is True

        # Verify subscriber was removed
        with open(temp_subscribers_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["subscribers"]) == 0

    def test_returns_false_for_nonexistent_subscriber(self, temp_subscribers_file, monkeypatch):
        """Should return False when subscriber doesn't exist."""
        import main

        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", temp_subscribers_file)
        monkeypatch.setattr(main, "DATA_DIR", temp_subscribers_file.parent)

        result = main.remove_subscriber(99999)

        assert result is False


class TestLoadSubscribers:
    """Tests for load_subscribers function."""

    def test_loads_empty_file(self, temp_subscribers_file, monkeypatch):
        """Should load empty subscribers list."""
        import main

        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", temp_subscribers_file)
        monkeypatch.setattr(main, "DATA_DIR", temp_subscribers_file.parent)

        data = main.load_subscribers()

        assert data["subscribers"] == []
        assert data["sent_log"] == []

    def test_handles_missing_file(self, monkeypatch, tmp_path):
        """Should return default structure for missing file."""
        import main

        nonexistent = tmp_path / "nonexistent.json"
        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", nonexistent)
        monkeypatch.setattr(main, "DATA_DIR", tmp_path)

        data = main.load_subscribers()

        assert data == {"subscribers": [], "sent_log": []}


class TestSaveSubscribers:
    """Tests for save_subscribers function."""

    def test_saves_data_atomically(self, monkeypatch, tmp_path):
        """Should save data atomically to prevent corruption."""
        import main

        subscribers_file = tmp_path / "subscribers.json"
        subscribers_file.write_text('{"subscribers": [], "sent_log": []}', encoding="utf-8")

        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", subscribers_file)
        monkeypatch.setattr(main, "DATA_DIR", tmp_path)

        new_data = {
            "subscribers": [{"chat_id": 12345, "username": "test"}],
            "sent_log": []
        }

        main.save_subscribers(new_data)

        # Verify file was written correctly
        with open(subscribers_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data == new_data

    def test_preserves_data_on_repeated_saves(self, monkeypatch, tmp_path):
        """Data should persist through multiple save operations."""
        import main

        subscribers_file = tmp_path / "subscribers.json"
        subscribers_file.write_text('{"subscribers": [], "sent_log": []}', encoding="utf-8")

        monkeypatch.setattr(main, "SUBSCRIBERS_PATH", subscribers_file)
        monkeypatch.setattr(main, "DATA_DIR", tmp_path)

        # Save multiple times
        for i in range(5):
            data = main.load_subscribers()
            data["subscribers"].append({"chat_id": i, "username": f"user{i}"})
            main.save_subscribers(data)

        # Verify all data persists
        with open(subscribers_file, "r", encoding="utf-8") as f:
            final_data = json.load(f)

        assert len(final_data["subscribers"]) == 5
