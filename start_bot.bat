@echo off
cd /d "%~dp0"
echo Starting Trophy Bot...
start "TrophyBot" /B pythonw bot.py
echo Bot is running in the background. Check bot.log for activity.
