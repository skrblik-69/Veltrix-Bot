# Veltrix Discord Bot

## Overview
Veltrix is a multi-functional Discord bot written in Python using discord.py. It provides moderation, automod, ticketing, music, MDT (Mobile Data Terminal), and utility features.

## Project Structure
```
├── main.py           # Main bot entry point
├── database.py       # Database operations (SQLite via aiosqlite)
├── config.json       # Bot configuration
├── requirements.txt  # Python dependencies
├── cogs/             # Bot command modules
│   ├── automod.py    # Auto-moderation features
│   ├── mdt.py        # Mobile Data Terminal commands
│   ├── moderation.py # Moderation commands
│   ├── music.py      # Music playback commands
│   ├── tickets.py    # Ticket system
│   └── utility.py    # Utility commands
├── utils/            # Helper utilities
│   ├── helpers.py    # Helper functions
│   └── logging.py    # Logging configuration
├── data/             # Database storage
└── logs/             # Log files
```

## Setup Requirements

### Environment Variables
- `DISCORD_TOKEN` - Discord bot token (required)

### Dependencies
- discord.py>=2.3.0
- aiohttp>=3.8.0
- aiosqlite>=0.19.0
- yt-dlp>=2023.10.13
- python-dotenv>=1.0.0

## Running the Bot
The bot runs via `python main.py` and requires a valid Discord token set as an environment variable.

## Configuration
Edit `config.json` to customize:
- Command prefix
- Embed color
- Owner IDs
- Automod settings
- Ticket system settings
- Music settings
- MDT settings
- Welcome/goodbye messages

## Recent Changes
- 2026-01-02: Initial import to Replit, fixed security issue with hardcoded token
