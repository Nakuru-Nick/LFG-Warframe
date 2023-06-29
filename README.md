# LFG-Warframe

A Discord bot for managing and organizing Looking for Group (LFG) posts.

This bot allows users to create, filter, list, and delete LFG posts within a Discord server. The bot utilizes an SQLite database to store and retrieve LFG post information.

## Commands

- `$create`: Creates a new LFG post with a description, category, and timestamp.
- `$delete`: Deletes an existing LFG post based on its ID.
- `$list`: Lists all the available LFG posts.
- `$filter`: Filters LFG posts based on their category.
- `$set_lfg_channel`: Sets the channel where LFG posts can be created.
- `$set_active_channel`: Sets the channel where the bot listens for LFG commands.
- `$set_lfg_role`: Sets the role that is mentioned when a new LFG post is created.
- `$set_lfg_ping_role`: Sets the role that can be pinged for LFG posts.
- `$ping`: Checks the latency of the bot.
- `$about`: Displays information about the bot.

## Database Tables

The bot uses a SQLite database to store information about LFG posts and guild-specific settings. The following tables are used:

- `lfg_posts`: Stores information about LFG posts, including user ID, description, category, timestamp, and channel ID.
- `guilds`: Stores guild-specific settings, including LFG channel ID and active channel ID.

## Setup

1. Clone the repository:

```shell
git clone https://github.com/Nakuru-Nick/LFG-Warframe.git
cd LFG-Warframe

```

2. Install the dependencies:

```shell
pip install -r requirements.txt
```

3. Create a Discord bot and obtain a bot token. Follow the instructions in the [Discord Developer Portal](https://discord.com/developers/applications) to create a new bot.

4. Create a `.env` file in the project root directory and add the following environment variables:

```shell
DISCORD_TOKEN=your_bot_token_here
```

5. Run the bot:

```shell
LFG Bot Main.py
```

## Contributing

Contributions are welcome! If you have any suggestions, bug reports, or feature requests, please open an issue or submit a pull request.
