from telegram import Update
from telegram.ext import ContextTypes
from db import add_entry, delete_last_entry, get_current_standings, get_user_history
from summary import post_summary, post_projection, _standings_text


async def cmd_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    raw = " ".join(context.args).strip() if context.args else ""

    if not raw.lstrip("-").isdigit():
        await update.message.reply_text("Usage: /add <number>  e.g. /add 42")
        return

    trophies = int(raw)
    if trophies < 0:
        await update.message.reply_text("Trophy count can't be negative!")
        return

    # Use the message's original send time so backlogged messages get the right timestamp
    add_entry(str(user.id), user.first_name, trophies, submitted_at=update.message.date)
    await update.message.reply_text(f"Recorded! {user.first_name}: {trophies} 🏆")


async def cmd_undo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    deleted = delete_last_entry(str(user.id))

    if deleted is None:
        await update.message.reply_text("You don't have any entries to undo.")
        return

    trophies, _ = deleted
    await update.message.reply_text(f"Undone! Removed your last entry: {trophies} 🏆")


async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    standings = get_current_standings()
    text = "🏆 *Leaderboard*\n\n" + _standings_text(standings)
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await post_summary(context.bot, update.effective_chat.id, header="📊 *Trophy Summary*")


async def cmd_projection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await post_projection(context.bot, update.effective_chat.id)


async def cmd_mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    history = get_user_history(str(user.id))

    if not history:
        await update.message.reply_text("No entries yet — use /add <number> to log your trophies!")
        return

    lines = [f"📊 *Your history, {user.first_name}:*\n"]
    for trophies, submitted_at in history:
        date = submitted_at[:10]
        lines.append(f"• {trophies} 🏆  on {date}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🏆 *Trophy Tracker*\n\n"
        "/add <number> — Log your trophy count  e.g. /add 42\n"
        "/undo — Remove your own last entry\n"
        "/leaderboard — Current standings with catch-up %\n"
        "/summary — Full summary with charts\n"
        "/projection — Catch-up projection chart\n"
        "/mystats — Your own submission history\n"
        "/help — Show this message\n\n"
        "Tip: just send a number (e.g. `42`) as a shortcut for /add\n"
        "If the bot was offline when you sent your score, it will catch up automatically when it restarts."
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def plain_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.lstrip("-").isdigit():
        return

    user = update.effective_user
    trophies = int(text)
    if trophies < 0:
        await update.message.reply_text("Trophy count can't be negative!")
        return

    add_entry(str(user.id), user.first_name, trophies, submitted_at=update.message.date)
    await update.message.reply_text(f"Recorded! {user.first_name}: {trophies} 🏆")
