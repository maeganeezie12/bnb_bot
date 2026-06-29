# Product Requirements Document — Trophy Tracker Telegram Bot

## Overview

A always-on Telegram bot that lets users log trophy counts at any time. Every 2 days, the bot automatically posts a summary to the group with current standings and a graphical chart showing progress.

---

## Goals

- Zero friction for users — one command to submit a number, anytime
- Persistent tracking — all submissions are stored and timestamped
- Automated bi-daily summaries with visual standings
- No manual admin action required once the bot is running

---

## Users

- Members of a Telegram group (family, friends, or a team)
- Each Telegram user is identified by their username/display name

---

## Core Features

### 1. Trophy Submission

- **Trigger:** User sends `/add <number>` or just a plain number in the chat
- **Behavior:**
  - Bot records the value with the user's name and a timestamp
  - Bot replies with a confirmation: `"Recorded! [Username]: 42 trophies"`
  - Users can submit as many times as they want — each entry is logged separately
  - The latest submission per user is treated as their current standing

### 2. Always-On Operation

- The bot runs as a persistent process (e.g., a long-polling or webhook service)
- It must reconnect automatically on network drops or restarts
- All data is persisted to a local database (SQLite) so no entries are lost between restarts

### 3. Bi-Daily Automated Summary

- **Schedule:** Every 2 days at a fixed time (configurable, default: 8:00 PM local time)
- **Content:**
  1. Ranked leaderboard of all users by current trophy count (highest first)
  2. Delta from each user's previous summary (e.g., `+5`, `-3`, `new`)
  3. Bar chart image showing trophy counts per user
  4. Line chart image showing each user's trophy count trend over the last 4 summaries (if data exists)
- **Delivery:** Posted as a message + image(s) in the group chat

### 4. Catch-Up Percentage

- Every summary and leaderboard shows each user's gap to the leader, expressed as a percentage
- Formula: `catch_up_% = ((leader_trophies - user_trophies) / leader_trophies) × 100`
- Displayed inline next to each non-leader entry, e.g.:
  ```
  1. Alice — 120 🏆
  2. Bob   —  95 🏆  (needs +25 to catch up, 20.8% behind)
  3. Carol —  60 🏆  (needs +60 to catch up, 50.0% behind)
  ```
- Leader shows `"👑 Leading"` instead of a percentage
- If two users are tied with the leader, both show `"👑 Tied for lead"`

### 5. Manual Summary on Demand

- **Trigger:** `/summary` command (any user can invoke)
- **Behavior:** Posts the same summary format immediately, without resetting the 2-day timer

### 5. Leaderboard on Demand

- **Trigger:** `/leaderboard` command
- **Behavior:** Posts a plain-text ranked list of current standings (no chart)

---

## Commands

| Command | Description |
|---|---|
| `/add <number>` | Log your current trophy count |
| `/summary` | Trigger an immediate summary with charts |
| `/leaderboard` | Show current standings with catch-up % to the leader |
| `/help` | List available commands |
| `/mystats` | Show your own submission history |

Plain integers (e.g. `42`) sent without a command are also accepted as a shortcut for `/add`.

---

## Data Model

### `entries` table

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `user_id` | TEXT | Telegram user ID |
| `username` | TEXT | Display name at time of submission |
| `trophies` | INTEGER | Trophy count submitted |
| `submitted_at` | DATETIME | UTC timestamp of submission |

### `summaries` table

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `posted_at` | DATETIME | When the summary was posted |
| `snapshot_json` | TEXT | JSON snapshot of standings at that moment |

---

## Charts

Generated using `matplotlib` and sent as PNG images via Telegram's `sendPhoto` API.

### Bar Chart
- X-axis: usernames
- Y-axis: current trophy count (latest submission per user)
- Bars colored by rank (gold / silver / bronze for top 3, grey for rest)
- Each bar is annotated with the trophy count and catch-up % (e.g. `95 | -20.8%`) except the leader which shows `👑`
- Title: `"Current Standings — [Date]"`

### Line Chart (Trend)
- X-axis: summary dates (last 4 bi-daily summaries)
- Y-axis: trophy count
- One line per user, labeled
- Title: `"Trophy Trends — Last 4 Summaries"`
- Only shown if at least 2 prior summaries exist

---

## Non-Functional Requirements

- **Persistence:** SQLite database; survives bot restarts without data loss
- **Availability:** Bot must auto-restart on crash (run via `systemd`, `pm2`, or equivalent process manager)
- **Timezone:** Configurable via `.env` (default: `Asia/Hong_Kong`)
- **Rate limiting:** Accept unlimited submissions per user per day — no restrictions
- **Error handling:** Invalid inputs (non-integers) get a friendly error reply; bot never crashes on bad input

---

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Telegram library | `python-telegram-bot` (v21+, async) |
| Database | SQLite via `sqlite3` (stdlib) |
| Scheduler | `APScheduler` or `python-telegram-bot` JobQueue |
| Charts | `matplotlib` |
| Config | `.env` file via `python-dotenv` |

---

## Configuration (`.env`)

```
TELEGRAM_BOT_TOKEN=...
GROUP_CHAT_ID=...
SUMMARY_TIME=20:00          # 24h HH:MM, local time
SUMMARY_INTERVAL_DAYS=2
TIMEZONE=Asia/Hong_Kong
```

---

## Out of Scope (v1)

- Web dashboard
- Multiple groups / multi-tenancy
- Trophy categories or game-specific tracking
- Authentication or admin roles
- Push notifications outside of Telegram
