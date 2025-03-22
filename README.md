# Alt Checker Bot

A powerful Discord bot for checking Minecraft player statistics and managing alternate accounts. The bot provides detailed Bedwars statistics, alt checking capabilities, and server management features.

## Features

- **Bedwars Statistics**: View detailed Bedwars stats including W/L ratio, FKDR, BBLR, and more
- **Alt Checking**: Identify potential alternate accounts
- **Skin Rendering**: Customizable skin renders with multiple styles
- **Server Management**: Announcements, polls, and message management
- **Suggestion System**: Built-in feature suggestion system
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Commands

### Alt Checker
- `/altcheck <username>`: Check for potential alternate accounts

### Player Statistics
- `/bedwars <username>`: View detailed Bedwars statistics for a player

### Utility
- `/ping`: Check the bot's latency
- `/help`: View all available commands and their descriptions
- `/info`: Display information about the bot

### Settings
- `/setrender <username> <render_type>` (Dev Only): Change skin render type

### Community
- `/suggest <suggestion>`: Suggest new features or improvements
- `/requestchange <username> <render_type>`: Request a skin render change
  - Available render types: default, walking, cheering, sleeping
- `/discord`: Get the bot's invite link

### Server (Requires Admin Permissions)
- `/announce <channel> <message>`: Make server announcements
- `/poll <question> <option1> <option2> [option3] [option4]`: Create server polls
- `/clear <amount> [channel]`: Clear messages in a channel (1-100)

## Setup

1. Clone the repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Get a [Polsu API Key](https://polsu.xyz/api/apikey) and a [Urchin Key](https://discord.gg/zVxT5n9J39)
4. Create a `.env` file in `\acm\config` with your the following:
   ```
POLSU_KEY=your_key_here
URCHIN_KEY=your_key_here
TOKEN=your_token_here
SUGGESTIONS=your_channel_here
RENDERS=your_channel_here
ADMIN_IDS=your_id_here
   ```
5. Run the bot:
   ```bash
   py acm.py
   ```

## Development

The bot is built with:
- Python 3.8+
- discord.py
- aiohttp
- Other dependencies listed in requirements.txt

## Examples


## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For support, contact the developer via Discord:  
[Contact Developer](https://discord.gg/BXTeeSBPWE/)
