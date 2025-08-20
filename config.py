import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
TRANSCRIPT_CHANNEL = int(os.getenv('TRANSCRIPT_CHANNEL'))
TICKET_CATEGORY = int(os.getenv('TICKET_CATEGORY'))
STAFF_ROLE = int(os.getenv('STAFF_ROLE'))

# Modmail configuration
BLOCKED_USERS = set()  # You can store this in a database later
MODMAIL_EMBED_COLOR = 0x00ff00  # Green
ERROR_EMBED_COLOR = 0xff0000   # Red
INFO_EMBED_COLOR = 0x0099ff    # Blue