"""
Telegram Bot for "jueehanbeoneun" (Once a Week)
Sends weekly questions to help users connect with their parents.
"""

import json
import os
import random
import logging
import tempfile
import shutil
import asyncio
from datetime import datetime, timedelta
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
CATEGORY_LABELS = {"past": "과거", "present": "현재", "future": "미래"}
DIFFICULTY_LABELS = {1: "가벼움", 2: "중간", 3: "깊음"}
DAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]

# Data storage paths (from config)
DATA_DIR = config.BOT_DIR / "data"
SUBSCRIBERS_PATH = config.SUBSCRIBERS_JSON_PATH
QUESTIONS_PATH = config.QUESTIONS_JSON_PATH


def ensure_data_dir():
    """Ensure data directory exists."""
    DATA_DIR.mkdir(exist_ok=True)


def load_questions() -> list:
    """Load questions from JSON file."""
    try:
        with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("questions", [])
    except FileNotFoundError:
        logger.error(f"Questions file not found: {QUESTIONS_PATH}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in questions file: {QUESTIONS_PATH}")
        return []


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

    # Write to temporary file first
    temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, suffix=".json")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Atomic replace (safe even on Windows)
        shutil.move(temp_path, SUBSCRIBERS_PATH)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def add_subscriber(chat_id: int, username: str = None) -> bool:
    """Add a new subscriber. Returns True if new, False if already exists."""
    data = load_subscribers()

    # Check if already subscribed
    for sub in data["subscribers"]:
        if sub["chat_id"] == chat_id:
            return False

    # Add new subscriber
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


def get_question_for_date(questions: list, date: datetime) -> dict:
    """Get a deterministic question for a specific date."""
    if not questions:
        return None

    start_date = datetime(2024, 12, 12)
    diff_days = (date - start_date).days
    index = diff_days % len(questions)
    return questions[index]


def get_week_questions(questions: list) -> list:
    """Get questions for the current week (Mon-Sun)."""
    today = datetime.now()

    # Find Monday of current week
    monday = today - timedelta(days=today.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    week_questions = []
    for i in range(7):
        date = monday + timedelta(days=i)
        question = get_question_for_date(questions, date)
        is_today = date.date() == today.date()
        is_past = date.date() < today.date()

        week_questions.append({
            "date": date,
            "day_name": DAYS_KO[i],
            "question": question,
            "is_today": is_today,
            "is_past": is_past,
            "is_future": not is_today and not is_past
        })

    return week_questions


def get_random_question(questions: list, exclude_id: int = None) -> dict:
    """Get a random question, optionally excluding one."""
    if not questions:
        return None

    filtered = [q for q in questions if q["id"] != exclude_id] if exclude_id else questions
    return random.choice(filtered) if filtered else questions[0]


def format_question_message(question: dict, title: str = "오늘의 질문") -> str:
    """Format a question for display."""
    if not question:
        return "질문을 불러올 수 없습니다."

    category = CATEGORY_LABELS.get(question["category"], "")
    difficulty = DIFFICULTY_LABELS.get(question["difficulty"], "")

    return (
        f"🐦 *{title}*\n\n"
        f"_{question['text']}_\n\n"
        f"📂 {category} | ⭐ {difficulty}"
    )


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    is_new = add_subscriber(chat_id, user.username)

    if is_new:
        welcome_text = (
            f"안녕하세요, {user.first_name}님! 🐦\n\n"
            "*주에한번은*에 오신 것을 환영해요.\n\n"
            "매주 월요일 오전, 부모님께 보낼 수 있는\n"
            "따뜻한 질문을 보내드릴게요.\n\n"
            "📌 *명령어*\n"
            "/question - 지금 바로 질문 받기\n"
            "/week - 이번 주 질문 보기\n"
            "/stop - 구독 취소\n\n"
            "효도는 빈도입니다 💕"
        )
    else:
        welcome_text = (
            f"다시 오셨네요, {user.first_name}님! 🐦\n\n"
            "이미 구독 중이시네요.\n\n"
            "📌 *명령어*\n"
            "/question - 지금 바로 질문 받기\n"
            "/week - 이번 주 질문 보기\n"
            "/stop - 구독 취소"
        )

    keyboard = [
        [InlineKeyboardButton("✨ 오늘의 질문 받기", callback_data="get_question")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def question_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /question command - get today's question."""
    questions = load_questions()
    today = datetime.now()
    question = get_question_for_date(questions, today)

    message = format_question_message(question)

    keyboard = [
        [
            InlineKeyboardButton("📋 복사하기", callback_data=f"copy_{question['id']}"),
            InlineKeyboardButton("🔄 다른 질문", callback_data="random_question")
        ],
        [InlineKeyboardButton("✅ 보냈어요!", callback_data=f"sent_{question['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /week command - show this week's questions."""
    questions = load_questions()
    week = get_week_questions(questions)

    lines = ["📅 *이번 주 질문들*\n"]

    for item in week:
        date_str = item["date"].strftime("%m/%d")

        if item["is_today"]:
            prefix = "▶️"
            text = item["question"]["text"][:30] + "..." if len(item["question"]["text"]) > 30 else item["question"]["text"]
        elif item["is_past"]:
            prefix = "✅"
            text = item["question"]["text"][:30] + "..." if len(item["question"]["text"]) > 30 else item["question"]["text"]
        else:
            prefix = "⏳"
            text = "(예정)"

        lines.append(f"{prefix} *{item['day_name']}* {date_str}: {text}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command - unsubscribe."""
    chat_id = update.effective_chat.id
    removed = remove_subscriber(chat_id)

    if removed:
        await update.message.reply_text(
            "구독이 취소되었어요. 😢\n\n"
            "다시 시작하려면 /start 를 입력해주세요."
        )
    else:
        await update.message.reply_text(
            "구독 중이 아니에요.\n"
            "시작하려면 /start 를 입력해주세요."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🐦 *주에한번은* 도움말\n\n"
        "부모님께 보낼 따뜻한 질문을\n"
        "매주 추천해드려요.\n\n"
        "📌 *명령어*\n"
        "/start - 구독 시작\n"
        "/question - 오늘의 질문 받기\n"
        "/week - 이번 주 질문 보기\n"
        "/stop - 구독 취소\n"
        "/help - 도움말\n\n"
        "💡 매주 월요일 오전 9시에\n"
        "자동으로 질문을 보내드려요!"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")


# Callback query handlers
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data
    questions = load_questions()

    if data == "get_question":
        # Get today's question
        today = datetime.now()
        question = get_question_for_date(questions, today)
        message = format_question_message(question)

        keyboard = [
            [
                InlineKeyboardButton("📋 복사하기", callback_data=f"copy_{question['id']}"),
                InlineKeyboardButton("🔄 다른 질문", callback_data="random_question")
            ],
            [InlineKeyboardButton("✅ 보냈어요!", callback_data=f"sent_{question['id']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    elif data == "random_question":
        # Get a random different question
        current_id = context.user_data.get("current_question_id")
        question = get_random_question(questions, current_id)
        context.user_data["current_question_id"] = question["id"]

        message = format_question_message(question, "다른 질문")

        keyboard = [
            [
                InlineKeyboardButton("📋 복사하기", callback_data=f"copy_{question['id']}"),
                InlineKeyboardButton("🔄 다른 질문", callback_data="random_question")
            ],
            [InlineKeyboardButton("✅ 보냈어요!", callback_data=f"sent_{question['id']}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    elif data.startswith("copy_"):
        question_id = int(data.split("_")[1])
        question = next((q for q in questions if q["id"] == question_id), None)

        if question:
            # Send the question text as a separate message for easy copying
            await query.message.reply_text(
                question["text"],
                parse_mode=None  # Plain text for easy copying
            )
            await query.answer("질문이 전송되었어요! 위 메시지를 복사하세요.", show_alert=False)
        else:
            await query.answer("질문을 찾을 수 없어요.", show_alert=True)

    elif data.startswith("sent_"):
        question_id = int(data.split("_")[1])
        await query.answer("잘하셨어요! 부모님이 기뻐하실 거예요 💕", show_alert=True)

        # Update sent count for subscriber
        chat_id = update.effective_chat.id
        subscribers_data = load_subscribers()
        for sub in subscribers_data["subscribers"]:
            if sub["chat_id"] == chat_id:
                sub["sent_count"] = sub.get("sent_count", 0) + 1
                break
        save_subscribers(subscribers_data)


# Scheduled notification helpers
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
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Retry {attempt + 1}/{max_retries} for {chat_id}: {e}")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to send to {chat_id} after {max_retries} attempts: {e}")
                return False


async def send_weekly_notification(context: ContextTypes.DEFAULT_TYPE):
    """Send weekly question notification to all subscribers."""
    questions = load_questions()
    today = datetime.now()
    question = get_question_for_date(questions, today)

    message = (
        "🐦 *주에한번은* - 이번 주 질문이 도착했어요!\n\n"
        f"_{question['text']}_\n\n"
        f"📂 {CATEGORY_LABELS.get(question['category'], '')} | "
        f"⭐ {DIFFICULTY_LABELS.get(question['difficulty'], '')}\n\n"
        "이번 주에 부모님께 보내보세요 💕"
    )

    keyboard = [
        [
            InlineKeyboardButton("📋 복사하기", callback_data=f"copy_{question['id']}"),
            InlineKeyboardButton("🔄 다른 질문", callback_data="random_question")
        ],
        [InlineKeyboardButton("✅ 보냈어요!", callback_data=f"sent_{question['id']}")]
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

    logger.info(f"Weekly notification: {sent_count} sent, {failed_count} failed")


async def post_init(application: Application):
    """Post initialization hook to start scheduler."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_weekly_notification,
        "cron",
        day_of_week=config.WEEKLY_NOTIFICATION_DAY,
        hour=config.WEEKLY_NOTIFICATION_HOUR,
        minute=config.WEEKLY_NOTIFICATION_MINUTE,
        args=[application]
    )
    scheduler.start()
    logger.info(f"Weekly notifications scheduled for: "
                f"{DAYS_KO[config.WEEKLY_NOTIFICATION_DAY]} "
                f"{config.WEEKLY_NOTIFICATION_HOUR:02d}:{config.WEEKLY_NOTIFICATION_MINUTE:02d}")


def main():
    """Start the bot."""
    # Create application with post_init hook
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("question", question_command))
    application.add_handler(CommandHandler("week", week_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("help", help_command))

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot started!")

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
