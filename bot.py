import os
import logging
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from pathlib import Path
from db import init_db
from handlers import cmd_add, cmd_leaderboard, cmd_summary, cmd_mystats, cmd_help, plain_number
from summary import post_summary

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(Path(__file__).parent / "bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))
SUMMARY_INTERVAL_DAYS = int(os.getenv("SUMMARY_INTERVAL_DAYS", "2"))


async def scheduled_summary(context):
    await post_summary(context.bot, GROUP_CHAT_ID)


def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("add", cmd_add))
    app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CommandHandler("mystats", cmd_mystats))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, plain_number))

    interval_seconds = SUMMARY_INTERVAL_DAYS * 24 * 60 * 60
    app.job_queue.run_repeating(
        scheduled_summary,
        interval=interval_seconds,
        first=interval_seconds,
    )

    logging.info("Bot is running. Press Ctrl+C to stop.")
    # drop_pending_updates=False so messages sent while offline are processed with their original timestamps
    app.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
