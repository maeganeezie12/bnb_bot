"""Shared summary-posting logic used by both the scheduler and /summary command."""
from telegram import Bot, InputMediaPhoto
from db import get_current_standings, save_summary, get_recent_summaries
from charts import bar_chart, trend_chart, projection_chart


def _standings_text(standings) -> str:
    if not standings:
        return "No entries yet — use /add <number> to log your trophies!"

    leader = standings[0][2]
    medals = ["🥇", "🥈", "🥉"]
    lines = []

    for i, (_, username, trophies, _) in enumerate(standings):
        medal = medals[i] if i < 3 else f"{i + 1}."
        if i == 0:
            line = f"{medal} *{username}* — {trophies} 🏆  👑 Leading"
        else:
            gap = leader - trophies
            pct = gap / leader * 100
            line = f"{medal} *{username}* — {trophies} 🏆  (needs +{gap}, {pct:.1f}% behind)"
        lines.append(line)

    return "\n".join(lines)


async def post_summary(bot: Bot, chat_id: int, header: str = "📊 *Bi-Daily Trophy Summary*"):
    standings = get_current_standings()

    if not standings:
        await bot.send_message(chat_id, "No trophy entries yet!")
        return

    snapshot = [{"user_id": r[0], "username": r[1], "trophies": r[2]} for r in standings]
    save_summary(snapshot)

    text = f"{header}\n\n{_standings_text(standings)}"

    bar = bar_chart(standings)
    summaries = get_recent_summaries(None)
    trend = trend_chart(summaries)

    photos = [p for p in (bar, trend) if p]

    if not photos:
        await bot.send_message(chat_id, text, parse_mode="Markdown")
    elif len(photos) == 1:
        await bot.send_photo(chat_id, photos[0], caption=text, parse_mode="Markdown")
    else:
        media = [InputMediaPhoto(photos[0], caption=text, parse_mode="Markdown")]
        media += [InputMediaPhoto(p) for p in photos[1:]]
        await bot.send_media_group(chat_id, media)


async def post_projection(bot: Bot, chat_id: int):
    summaries = get_recent_summaries(None)
    projection = projection_chart(summaries)

    if not projection:
        await bot.send_message(chat_id, "Not enough history yet to project a catch-up — keep logging trophies!")
        return

    await bot.send_photo(chat_id, projection, caption="🔮 *Catch-Up Projection*", parse_mode="Markdown")
