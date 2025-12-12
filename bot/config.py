# Telegram Bot Configuration v2.0
import os
from pathlib import Path

# Load from environment variable (secure)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# Bot settings
BOT_USERNAME = "mwohae_bot"
WEB_URL = "https://aidenvibe.github.io/once-a-week/"

# Scheduler settings - Daily at 19:00 (7 PM)
DAILY_NOTIFICATION_HOUR = 19
DAILY_NOTIFICATION_MINUTE = 0

# Data paths
BOT_DIR = Path(__file__).parent.resolve()
DEFAULT_QUESTIONS_PATH = BOT_DIR / "data" / "questions.json"
DEFAULT_SUBSCRIBERS_PATH = BOT_DIR / "data" / "subscribers.json"

# Environment variables override defaults
QUESTIONS_JSON_PATH = Path(os.environ.get("QUESTIONS_PATH", str(DEFAULT_QUESTIONS_PATH)))
SUBSCRIBERS_JSON_PATH = Path(os.environ.get("SUBSCRIBERS_PATH", str(DEFAULT_SUBSCRIBERS_PATH)))
