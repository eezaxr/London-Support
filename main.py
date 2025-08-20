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
        
        # Special user who can run all commands
        self.special_user_id = 790869950076157983
        
        # Channel ID for whitelist auto-response
        self.whitelist_channel_id = 1384510906897137745
        
    async def setup_hook(self):
        """Load all command cogs and set status"""
        try:
            # Load all command files
            command_files = [
                'commands.reply',
                'commands.close',
                'commands.claim',
                'commands.repair',
                'commands.role'  # Add this line
            ]
            
            for extension in command_files:
                try:
                    await self.load_extension(extension)
                    print(f"✅ Loaded {extension}")
                except Exception as e:
                    print(f"❌ Failed to load {extension}: {e}")
            
            # Set the status here in setup_hook instead of on_ready
            activity = discord.Game(name="DM For Support")
            await self.change_presence(activity=activity, status=discord.Status.online)
            print("✅ Bot status set in setup_hook")
            
        except Exception as e:
            print(f"Error in setup_hook: {e}")

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')
        print(f'Bot started at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Backup status setting with retry logic
        await asyncio.sleep(2)  # Wait a bit before setting status
        try:
            activity = discord.Game(name="DM For Support")
            await self.change_presence(activity=activity, status=discord.Status.online)
            print("✅ Bot status set in on_ready (backup)")
        except Exception as e:
            print(f"❌ Failed to set status: {e}")
            # Retry after 5 seconds
            await asyncio.sleep(5)
            try:
                activity = discord.Game(name="DM For Support")
                await self.change_presence(activity=activity, status=discord.Status.online)
                print("✅ Bot status set after retry")
            except Exception as e:
                print(f"❌ Failed to set status after retry: {e}")
        
        # Validate environment variables
        required_env_vars = ['GUILD_ID', 'TICKET_CATEGORY', 'STAFF_ROLE']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        else:
            print("✅ All required environment variables found")
        
    async def on_command_error(self, ctx, error):
        """Handle command errors globally"""
        if isinstance(error, commands.CommandNotFound):
            # Silently ignore CommandNotFound errors
            return
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to use this command or it's not available in this channel.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        else:
            print(f"Unhandled error in command {ctx.command}: {error}")
        
    async def on_message(self, message):
        # Process commands first
        await self.process_commands(message)
        
        # Handle specific channel auto-response
        if message.channel.id == self.whitelist_channel_id and not message.author.bot:
            try:
                await message.channel.send("To become Whitelisted, please apply here: <#1384509015962288210>, if you need support, please DM the support bot. Please speak in <#1384510906897137745>")
                print(f"✅ Sent whitelist message for user {message.author} in channel {message.channel.name}")
            except Exception as e:
                print(f"❌ Failed to send whitelist message: {e}")
        
        # Handle DM messages for modmail
        elif isinstance(message.channel, discord.DMChannel) and not message.author.bot:
            await self.handle_dm_message(message)
    
    async def handle_dm_message(self, message):
        """Handle incoming DM messages and forward them to modmail threads"""
        try:
            guild_id = os.getenv('GUILD_ID')
            if not guild_id:
                print("❌ GUILD_ID not set in environment variables")
                return
                
            guild = self.get_guild(int(guild_id))
            if not guild:
                print(f"❌ Could not find guild with ID {guild_id}")
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
                # Validate category exists
                category_id = os.getenv('TICKET_CATEGORY')
                if not category_id:
                    print("❌ TICKET_CATEGORY not set in environment variables")
                    return
                
                try:
                    category = guild.get_channel(int(category_id))
                    if not category:
                        print(f"❌ Could not find category with ID {category_id}")
                        return
                    
                    # Check if it's actually a category
                    if not isinstance(category, discord.CategoryChannel):
                        print(f"❌ Channel {category_id} is not a category channel")
                        return
                        
                except ValueError:
                    print(f"❌ Invalid TICKET_CATEGORY ID: {category_id}")
                    return
                
                # Validate staff role exists
                staff_role_id = os.getenv('STAFF_ROLE')
                if not staff_role_id:
                    print("❌ STAFF_ROLE not set in environment variables")
                    return
                
                try:
                    staff_role = guild.get_role(int(staff_role_id))
                    if not staff_role:
                        print(f"❌ Could not find staff role with ID {staff_role_id}")
                        return
                except ValueError:
                    print(f"❌ Invalid STAFF_ROLE ID: {staff_role_id}")
                    return
                
                # Get the specific user to add to all tickets
                auto_add_user_id = self.special_user_id
                auto_add_user = guild.get_member(auto_add_user_id)
                
                # Create ticket channel with permission overwrites
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                    guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }
                
                # Add the specific user to the ticket permissions if they exist in the guild
                if auto_add_user:
                    overwrites[auto_add_user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    print(f"✅ Added user {auto_add_user} to ticket permissions")
                else:
                    print(f"⚠️ User with ID {auto_add_user_id} not found in guild, but ticket will still be created")
                
                try:
                    ticket_channel = await guild.create_text_channel(
                        name=f"ticket-{user_id}",
                        category=category,
                        overwrites=overwrites
                    )
                except discord.HTTPException as e:
                    print(f"❌ Failed to create ticket channel: {e}")
                    return
                
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
            print(f"❌ Error handling DM: {e}")

    def is_staff_or_special_user(self, user_id, guild):
        """Check if user is staff or the special user who can run all commands"""
        # Always allow the special user
        if user_id == self.special_user_id:
            return True
        
        # Check if user has staff role
        staff_role_id = os.getenv('STAFF_ROLE')
        if not staff_role_id:
            return False
        
        try:
            staff_role = guild.get_role(int(staff_role_id))
            if not staff_role:
                return False
            
            member = guild.get_member(user_id)
            if member and staff_role in member.roles:
                return True
        except ValueError:
            return False
        
        return False

    async def check_command_permissions(self, ctx):
        """Check if user can run modmail commands"""
        # Allow in DMs for help/uptime commands
        if isinstance(ctx.channel, discord.DMChannel):
            return ctx.command.name in ['help', 'uptime']
        
        # Check if it's a ticket channel
        if not ctx.channel.name.startswith('ticket-'):
            return ctx.command.name in ['help', 'uptime']
        
        # Check if user is staff or special user
        return self.is_staff_or_special_user(ctx.author.id, ctx.guild)

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Custom help command"""
        embed = discord.Embed(
            title="🤖 Modmail Bot Commands",
            description="Here are the available commands:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Staff Commands",
            value="• `?reply <message>` - Reply to a ticket\n"
                  "• `?a_reply <message>` - Send anonymous reply\n"
                  "• `?close [reason]` - Close a ticket\n"
                  "• `?claim` - Claim a ticket\n"
                  "• `?repair` - Repair bot issues",
            inline=False
        )
        
        embed.add_field(
            name="General",
            value="• `?help` - Show this help message\n"
                  "• `?uptime` - Show bot uptime\n"
                  "• `?toggle_whitelist` - Toggle whitelist auto-response",
            inline=False
        )
        
        embed.set_footer(text="Note: Staff commands only work in ticket channels")
        await ctx.send(embed=embed)

    @commands.command(name="uptime")
    async def uptime_command(self, ctx):
        """Show bot uptime"""
        uptime = get_uptime()
        embed = discord.Embed(
            title="⏰ Bot Uptime",
            description=f"Bot has been running for: **{uptime}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="toggle_whitelist")
    async def toggle_whitelist(self, ctx):
        """Toggle the whitelist auto-response feature"""
        # Check if user has permission (staff or special user)
        if not self.is_staff_or_special_user(ctx.author.id, ctx.guild):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Toggle the whitelist channel ID (set to None to disable, restore to enable)
        if self.whitelist_channel_id == 1400532622161215598:
            self.whitelist_channel_id = None
            status = "disabled"
            color = discord.Color.red()
        else:
            self.whitelist_channel_id = 1400532622161215598
            status = "enabled"
            color = discord.Color.green()
        
        embed = discord.Embed(
            title=f"🔄 Whitelist Auto-Response {status.title()}",
            description=f"The whitelist auto-response has been **{status}**.",
            color=color
        )
        
        if status == "enabled":
            embed.add_field(
                name="Channel", 
                value=f"<#{self.whitelist_channel_id}>",
                inline=False
            )
        
        await ctx.send(embed=embed)



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