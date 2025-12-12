# Telegram Bot Configuration
import os
from pathlib import Path

# Load from environment variable (secure)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Bot settings
BOT_USERNAME = "mwohae_bot"

# Scheduler settings
WEEKLY_NOTIFICATION_DAY = 0  # Monday (0 = Monday, 6 = Sunday)
WEEKLY_NOTIFICATION_HOUR = 9  # 9 AM
WEEKLY_NOTIFICATION_MINUTE = 0

# Data paths - use absolute paths resolved from this file's location
BOT_DIR = Path(__file__).parent.resolve()
DEFAULT_QUESTIONS_PATH = BOT_DIR.parent / "docs" / "data" / "questions.json"
DEFAULT_SUBSCRIBERS_PATH = BOT_DIR / "data" / "subscribers.json"

# Environment variables override defaults
QUESTIONS_JSON_PATH = Path(os.environ.get("QUESTIONS_PATH", str(DEFAULT_QUESTIONS_PATH)))
SUBSCRIBERS_JSON_PATH = Path(os.environ.get("SUBSCRIBERS_PATH", str(DEFAULT_SUBSCRIBERS_PATH)))
