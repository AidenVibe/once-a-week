"""
Telegram Bot for "jueehanbeoneun" (Once a Week) v2.0
Sends daily questions to help users connect with their parents.
"""

import json
import os
import logging
import tempfile
import shutil
import asyncio
from datetime import datetime
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constants
THEME_LABELS = {"past": "과거", "future": "미래", "holiday": "기념일"}
START_DATE = datetime(2024, 12, 12)

# Data storage paths
DATA_DIR = config.BOT_DIR / "data"
SUBSCRIBERS_PATH = config.SUBSCRIBERS_JSON_PATH
QUESTIONS_PATH = config.QUESTIONS_JSON_PATH


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


def load_questions() -> dict:
    """Load questions from JSON file (new schema with daily/special/holidays)."""
    try:
        with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "daily": data.get("questions", {}).get("daily", []),
                "special": data.get("questions", {}).get("special", []),
                "holidays": data.get("holidays", [])
            }
    except FileNotFoundError:
        logger.error(f"Questions file not found: {QUESTIONS_PATH}")
        return {"daily": [], "special": [], "holidays": []}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in questions file: {QUESTIONS_PATH}")
        return {"daily": [], "special": [], "holidays": []}


def load_subscribers() -> dict:
    """Load subscribers from JSON file."""
    ensure_data_dir()
    try:
        with open(SUBSCRIBERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"subscribers": [], "sent_log": []}


def save_subscribers(data: dict):
    """Save subscribers atomically to prevent data corruption."""
    ensure_data_dir()

    temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, suffix=".json")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        shutil.move(temp_path, SUBSCRIBERS_PATH)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def add_subscriber(chat_id: int, username: str = None) -> bool:
    """Add a new subscriber. Returns True if new, False if already exists."""
    data = load_subscribers()

    for sub in data["subscribers"]:
        if sub["chat_id"] == chat_id:
            return False

    data["subscribers"].append({
        "chat_id": chat_id,
        "username": username,
        "subscribed_at": datetime.now().isoformat(),
        "sent_count": 0
    })
    save_subscribers(data)
    return True


def remove_subscriber(chat_id: int) -> bool:
    """Remove a subscriber. Returns True if removed, False if not found."""
    data = load_subscribers()
    original_count = len(data["subscribers"])
    data["subscribers"] = [s for s in data["subscribers"] if s["chat_id"] != chat_id]

    if len(data["subscribers"]) < original_count:
        save_subscribers(data)
        return True
    return False


def get_days_since_start(date: datetime) -> int:
    """Get number of days since start date."""
    target = date.replace(hour=0, minute=0, second=0, microsecond=0)
    return (target - START_DATE).days


def get_daily_question(questions: dict, date: datetime) -> dict:
    """Get daily question for a specific date."""
    daily_list = questions.get("daily", [])
    if not daily_list:
        return None

    days = get_days_since_start(date)
    index = days % len(daily_list)
    return daily_list[index]


def get_special_question(questions: dict, date: datetime) -> dict:
    """Get special question for a specific date (holiday takes priority)."""
    # 1. Holiday check
    mmdd = date.strftime("%m-%d")
    holidays = questions.get("holidays", [])
    for holiday in holidays:
        if holiday.get("date") == mmdd:
            return {
                "text": holiday.get("question", ""),
                "theme": "holiday",
                "name": holiday.get("name", "")
            }

    # 2. Regular special question
    special_list = questions.get("special", [])
    if not special_list:
        return None

    days = get_days_since_start(date)
    index = days % len(special_list)
    return special_list[index]


def format_today_message(daily: dict, special: dict) -> str:
    """Format today's questions for display."""
    if not daily and not special:
        return "질문을 불러올 수 없습니다."

    theme_label = THEME_LABELS.get(special.get("theme", ""), "") if special else ""

    lines = [
        "오늘의 질문이 도착했어요!",
        "",
        "*일상 질문*",
        f"_{daily['text']}_" if daily else "-",
        "",
        f"*특별 질문* ({theme_label})" if theme_label else "*특별 질문*",
        f"_{special['text']}_" if special else "-",
        "",
        "_오늘 꼭 보내지 않아도 괜찮아요_"
    ]

    return "\n".join(lines)


# Command handlers (only /start and /stop)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    is_new = add_subscriber(chat_id, user.username)

    if is_new:
        welcome_text = (
            f"안녕하세요, {user.first_name}님!\n\n"
            "*주에한번은*에 오신 것을 환영해요.\n\n"
            "매일 저녁 7시, 부모님께 보낼 수 있는\n"
            "따뜻한 질문을 보내드릴게요.\n\n"
            "구독을 취소하려면 /stop 을 입력하세요.\n\n"
            "_효도는 빈도입니다_"
        )
    else:
        welcome_text = (
            f"다시 오셨네요, {user.first_name}님!\n\n"
            "이미 구독 중이시네요.\n\n"
            "구독을 취소하려면 /stop 을 입력하세요."
        )

    # Show today's questions
    questions = load_questions()
    today = datetime.now()
    daily = get_daily_question(questions, today)
    special = get_special_question(questions, today)

    keyboard = [
        [
            InlineKeyboardButton("일상 복사", callback_data=f"copy_daily_{daily['id']}" if daily else "none"),
            InlineKeyboardButton("특별 복사", callback_data=f"copy_special_{special['id']}" if special else "none")
        ],
        [InlineKeyboardButton("웹에서 보기", url=config.WEB_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send welcome first
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

    # Then send today's questions
    question_message = format_today_message(daily, special)
    await update.message.reply_text(
        question_message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - unsubscribe."""
    chat_id = update.effective_chat.id
    removed = remove_subscriber(chat_id)

    if removed:
        await update.message.reply_text(
            "구독이 취소되었어요.\n\n"
            "다시 시작하려면 /start 를 입력해주세요."
        )
    else:
        await update.message.reply_text(
            "구독 중이 아니에요.\n"
            "시작하려면 /start 를 입력해주세요."
        )


# Callback query handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "none":
        await query.answer("질문을 불러올 수 없어요.", show_alert=True)
        return

    questions = load_questions()

    if data.startswith("copy_daily_"):
        question_id = int(data.split("_")[2])
        daily_list = questions.get("daily", [])
        question = next((q for q in daily_list if q["id"] == question_id), None)

        if question:
            await query.message.reply_text(question["text"], parse_mode=None)
            await query.answer("일상 질문이 전송되었어요! 복사하세요.", show_alert=False)
        else:
            await query.answer("질문을 찾을 수 없어요.", show_alert=True)

    elif data.startswith("copy_special_"):
        question_id = int(data.split("_")[2])
        special_list = questions.get("special", [])
        question = next((q for q in special_list if q["id"] == question_id), None)

        if question:
            await query.message.reply_text(question["text"], parse_mode=None)
            await query.answer("특별 질문이 전송되었어요! 복사하세요.", show_alert=False)
        else:
            await query.answer("질문을 찾을 수 없어요.", show_alert=True)


# Scheduled notification
async def send_with_retry(bot, chat_id: int, message: str, reply_markup, max_retries: int = 3) -> bool:
    """Send message with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {chat_id}: {e}")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to send to {chat_id} after {max_retries} attempts: {e}")
                return False


async def send_daily_notification(context: ContextTypes.DEFAULT_TYPE):
    """Send daily question notification to all subscribers."""
    questions = load_questions()
    today = datetime.now()
    daily = get_daily_question(questions, today)
    special = get_special_question(questions, today)

    message = format_today_message(daily, special)

    keyboard = [
        [
            InlineKeyboardButton("일상 복사", callback_data=f"copy_daily_{daily['id']}" if daily else "none"),
            InlineKeyboardButton("특별 복사", callback_data=f"copy_special_{special['id']}" if special else "none")
        ],
        [InlineKeyboardButton("웹에서 보기", url=config.WEB_URL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    subscribers_data = load_subscribers()
    sent_count = 0
    failed_count = 0

    for sub in subscribers_data["subscribers"]:
        success = await send_with_retry(
            context.bot, sub["chat_id"], message, reply_markup
        )
        if success:
            sent_count += 1
        else:
            failed_count += 1

    logger.info(f"Daily notification: {sent_count} sent, {failed_count} failed")


async def post_init(application: Application):
    """Post initialization hook to start scheduler."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_notification,
        "cron",
        hour=config.DAILY_NOTIFICATION_HOUR,
        minute=config.DAILY_NOTIFICATION_MINUTE,
        args=[application]
    )
    scheduler.start()
    logger.info(f"Daily notifications scheduled for: "
                f"{config.DAILY_NOTIFICATION_HOUR:02d}:{config.DAILY_NOTIFICATION_MINUTE:02d}")


def main():
    """Start the bot."""
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Add command handlers (only /start and /stop)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot v2.0 started!")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
