# TrueBlue Discord Bot

## Overview

TrueBlue is a comprehensive Discord bot built with Python and discord.py, designed to provide complete server management functionality. The bot features an integrated economy system, automatic moderation, music playback, ticket support system, and various utility commands. It uses SQLite for data persistence and supports Czech language localization. The bot is designed for community servers that need robust moderation tools combined with engaging features like currency systems and music streaming.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Bot Framework
- **Framework**: Built on discord.py with hybrid commands supporting both prefix and slash commands
- **Architecture Pattern**: Cog-based modular design for feature separation and maintainability
- **Configuration**: JSON-based configuration system with externalized settings for easy deployment
- **Async Design**: Fully asynchronous architecture leveraging Python's asyncio for optimal performance

### Database Layer
- **Primary Database**: SQLite with custom Database class wrapper
- **Schema Design**: Normalized tables for users, economy, moderation logs, and guild settings
- **Connection Management**: Single connection instance with proper error handling and connection pooling
- **Data Persistence**: Automatic table creation and migration support

### Modular Cog System
- **AutoMod Cog**: Real-time message analysis with spam detection, bad word filtering, and behavioral monitoring
- **Economy Cog**: Virtual currency system with daily rewards, work commands, and balance management
- **Moderation Cog**: Administrative tools including kick, ban, mute with audit logging
- **Music Cog**: Audio streaming with queue management, volume control, and playback features
- **Tickets Cog**: Support ticket system with categorized channels and role-based access
- **Utility Cog**: Server information, user profiles, and administrative utilities

### Security & Moderation
- **Permission System**: Role-based access control with Discord permission integration
- **Auto-Moderation**: Configurable thresholds for spam, mentions, emojis, and caps detection
- **Audit Logging**: Comprehensive moderation action logging with timestamp and reason tracking
- **Rate Limiting**: Built-in spam protection with time-based message frequency analysis

### User Interface
- **Command Interface**: Dual support for prefix commands (!command) and Discord slash commands
- **Interactive Elements**: Discord UI components including buttons and dropdowns for ticket system
- **Embed Messaging**: Rich embed formatting for enhanced visual presentation
- **Error Handling**: User-friendly error messages with proper exception handling

## External Dependencies

### Core Dependencies
- **discord.py**: Primary Discord API wrapper for bot functionality
- **sqlite3**: Built-in SQLite database interface for data persistence
- **asyncio**: Asynchronous programming support for concurrent operations
- **aiohttp**: HTTP client for external API requests and web scraping

### Audio Dependencies
- **FFmpeg**: Required for audio processing and streaming capabilities
- **youtube-dl/yt-dlp**: YouTube video/audio extraction for music commands

### Development Tools
- **logging**: Python standard library for comprehensive log management
- **json**: Configuration file parsing and API response handling
- **re**: Regular expressions for text pattern matching and validation
- **datetime**: Time handling for cooldowns, timestamps, and scheduling

### Discord Integration
- **Discord Intents**: Message content, member updates, and voice state monitoring
- **Discord Permissions**: Integration with server permission system
- **Discord UI Components**: Buttons, dropdowns, and modals for interactive features

### Optional Integrations
- **YouTube API**: Enhanced music search and metadata retrieval
- **Spotify API**: Playlist integration and music discovery features
- **External Webhooks**: Integration with external logging and monitoring services