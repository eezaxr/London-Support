import discord
from discord.ext import commands
import os
import asyncio
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.helpers import send_dm_safely

# Load environment variables
load_dotenv()

start_time = time.time()

class ModmailBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.dm_messages = True
        
        super().__init__(
            command_prefix='?',
            intents=intents,
            help_command=None
        )
        
        # Store active tickets and claimed tickets
        self.active_tickets = {}
        self.claimed_tickets = {}  # ticket_channel_id: user_id
        
    async def setup_hook(self):
        """Load all command cogs"""
        try:
            # Load all command files
            command_files = [
                'commands.reply',
                'commands.close',
                'commands.claim',
                'commands.repair'
            ]
            
            for extension in command_files:
                await self.load_extension(extension)
                print(f"Loaded {extension}")
            
        except Exception as e:
            print(f"Error in setup_hook: {e}")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
        print(f'Bot started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
    async def on_message(self, message):
        # Process commands first
        await self.process_commands(message)
        
        # Handle DM messages for modmail
        if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
            await self.handle_dm_message(message)
    
    async def handle_dm_message(self, message):
        """Handle incoming DM messages and forward them to modmail threads"""
        try:
            guild = self.get_guild(int(os.getenv('GUILD_ID')))
            if not guild:
                return
            
            user_id = message.author.id
            
            # Check if user has an active ticket
            ticket_channel = None
            for channel in guild.text_channels:
                if channel.name == f"ticket-{user_id}":
                    ticket_channel = channel
                    break
            
            # If no active ticket, create one
            if not ticket_channel:
                category = guild.get_channel(int(os.getenv('TICKET_CATEGORY')))
                staff_role = guild.get_role(int(os.getenv('STAFF_ROLE')))
                
                # Create ticket channel
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                
                ticket_channel = await guild.create_text_channel(
                    name=f"ticket-{user_id}",
                    category=category,
                    overwrites=overwrites
                )
                
                # Send initial message
                embed = discord.Embed(
                    title="New Modmail Thread",
                    description=f"Thread created for {message.author.mention} ({message.author})",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=message.author.display_avatar.url)
                embed.add_field(name="User ID", value=user_id, inline=True)
                embed.add_field(name="Account Created", value=message.author.created_at.strftime("%Y-%m-%d"), inline=True)
                
                await ticket_channel.send(embed=embed)
                self.active_tickets[user_id] = ticket_channel.id
                
                # Send confirmation to user that ticket was created
                user_confirmation = discord.Embed(
                    title="📬 Modmail Ticket Created",
                    description="Your modmail ticket has been successfully created! A staff member will respond to you as soon as possible.",
                    color=discord.Color.green()
                )
                user_confirmation.add_field(
                    name="What happens next?",
                    value="• Your message has been forwarded to our staff team\n• You will receive a response here in DMs\n• Feel free to send additional messages if needed",
                    inline=False
                )
                user_confirmation.set_footer(text="Please be patient while we review your message")
                
                await send_dm_safely(message.author, embed=user_confirmation)
            
            # Forward the message to the ticket channel
            embed = discord.Embed(
                description=message.content,
                color=discord.Color.blue(),
                timestamp=message.created_at
            )
            embed.set_author(
                name=f"{message.author} ({message.author.id})",
                icon_url=message.author.display_avatar.url
            )
            
            await ticket_channel.send(embed=embed)
            
            # Handle attachments
            if message.attachments:
                for attachment in message.attachments:
                    await ticket_channel.send(f"📎 **Attachment:** {attachment.url}")
            
        except Exception as e:
            print(f"Error handling DM: {e}")

# Get uptime
def get_uptime():
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    uptime_delta = timedelta(seconds=uptime_seconds)
    
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Run the bot
if __name__ == "__main__":
    bot = ModmailBot()
    bot.run(os.getenv('DISCORD_TOKEN'))