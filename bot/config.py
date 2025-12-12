# Telegram Bot Configuration
import os

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

# Data paths
QUESTIONS_JSON_PATH = "../web/data/questions.json"
SUBSCRIBERS_JSON_PATH = "./data/subscribers.json"
