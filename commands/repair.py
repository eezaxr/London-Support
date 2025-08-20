import discord
from discord.ext import commands
import psutil
import platform
from utils.helpers import is_authorized_user
from config import MODMAIL_EMBED_COLOR
from main import get_uptime

class Repair(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="repair")
    @is_authorized_user(790869950076157983)
    async def repair(self, ctx):
        """System information and bot diagnostics (Owner only)"""
        try:
            # Get bot latency
            latency = round(self.bot.latency * 1000)
            
            # Get uptime
            uptime = get_uptime()
            
            # Get system info
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get Discord.py version
            discord_version = discord.__version__
            
            # Get Python version
            python_version = platform.python_version()
            
            # Get OS info
            os_info = f"{platform.system()} {platform.release()}"
            
            # Count active tickets
            guild = ctx.guild
            active_tickets = 0
            claimed_tickets = 0
            
            for channel in guild.text_channels:
                if channel.name.startswith("ticket-"):
                    active_tickets += 1
                    if hasattr(self.bot, 'claimed_tickets') and channel.id in self.bot.claimed_tickets:
                        claimed_tickets += 1
            
            # Create main embed
            embed = discord.Embed(
                title="🔧 Bot Diagnostics & Repair Info",
                color=MODMAIL_EMBED_COLOR,
                timestamp=discord.utils.utcnow()
            )
            
            # Bot Status
            embed.add_field(
                name="🤖 Bot Status",
                value=f"**Ping:** {latency}ms\n"
                      f"**Uptime:** {uptime}\n"
                      f"**Status:** Online ✅",
                inline=True
            )
            
            # System Resources
            embed.add_field(
                name="💻 System Resources",
                value=f"**RAM Usage:** {memory.percent}%\n"
                      f"**CPU Usage:** {cpu_percent}%\n"
                      f"**Available RAM:** {round(memory.available / (1024**3), 2)}GB",
                inline=True
            )
            
            # Version Information
            embed.add_field(
                name="📦 Version Info",
                value=f"**Discord.py:** {discord_version}\n"
                      f"**Python:** {python_version}\n"
                      f"**OS:** {os_info}",
                inline=True
            )
            
            # Modmail Statistics
            embed.add_field(
                name="📊 Modmail Stats",
                value=f"**Active Tickets:** {active_tickets}\n"
                      f"**Claimed Tickets:** {claimed_tickets}\n"
                      f"**Unclaimed Tickets:** {active_tickets - claimed_tickets}",
                inline=True
            )
            
            # Guild Information
            embed.add_field(
                name="🏰 Guild Info",
                value=f"**Total Members:** {guild.member_count}\n"
                      f"**Text Channels:** {len(guild.text_channels)}\n"
                      f"**Voice Channels:** {len(guild.voice_channels)}",
                inline=True
            )
            
            # Bot Permissions
            bot_member = guild.get_member(self.bot.user.id)
            perms = bot_member.guild_permissions
            
            key_perms = {
                "Manage Channels": perms.manage_channels,
                "Read Messages": perms.read_messages,
                "Send Messages": perms.send_messages,
                "Embed Links": perms.embed_links,
                "Attach Files": perms.attach_files,
                "Read Message History": perms.read_message_history
            }
            
            perm_status = []
            for perm, has_perm in key_perms.items():
                status = "✅" if has_perm else "❌"
                perm_status.append(f"{status} {perm}")
            
            embed.add_field(
                name="🔐 Key Permissions",
                value="\n".join(perm_status),
                inline=False
            )
            
            # Configuration Status
            from config import GUILD_ID, TRANSCRIPT_CHANNEL, TICKET_CATEGORY, STAFF_ROLE
            
            config_status = []
            config_status.append(f"✅ Guild ID: {GUILD_ID}")
            
            transcript_ch = self.bot.get_channel(TRANSCRIPT_CHANNEL)
            config_status.append(f"{'✅' if transcript_ch else '❌'} Transcript Channel: {transcript_ch.name if transcript_ch else 'Not Found'}")
            
            ticket_cat = self.bot.get_channel(TICKET_CATEGORY)
            config_status.append(f"{'✅' if ticket_cat else '❌'} Ticket Category: {ticket_cat.name if ticket_cat else 'Not Found'}")
            
            staff_role = guild.get_role(STAFF_ROLE)
            config_status.append(f"{'✅' if staff_role else '❌'} Staff Role: {staff_role.name if staff_role else 'Not Found'}")
            
            embed.add_field(
                name="⚙️ Configuration Status",
                value="\n".join(config_status),
                inline=False
            )
            
            # Footer
            embed.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Repair Command Error",
                description=f"An error occurred while generating diagnostics: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="restart", hidden=True)
    @is_authorized_user(790869950076157983)
    async def restart(self, ctx):
        """Restart the bot (Owner only)"""
        try:
            restart_embed = discord.Embed(
                title="🔄 Bot Restarting",
                description="Bot is restarting... This may take a few moments.",
                color=0xffaa00,
                timestamp=discord.utils.utcnow()
            )
            restart_embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
            restart_embed.set_footer(text="Bot will be back online shortly")
            
            await ctx.send(embed=restart_embed)
            
            # Close the bot gracefully
            await self.bot.close()
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Restart Error",
                description=f"An error occurred while restarting: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="status", hidden=True)
    @is_authorized_user(790869950076157983)
    async def status(self, ctx, *, status_text: str = None):
        """Change bot status (Owner only)"""
        try:
            if status_text is None:
                # Show current status
                current_activity = self.bot.activity
                current_status = self.bot.status
                
                status_embed = discord.Embed(
                    title="🎭 Current Bot Status",
                    color=MODMAIL_EMBED_COLOR
                )
                status_embed.add_field(
                    name="Status", 
                    value=str(current_status).title(), 
                    inline=True
                )
                status_embed.add_field(
                    name="Activity", 
                    value=str(current_activity) if current_activity else "None", 
                    inline=True
                )
                
                await ctx.send(embed=status_embed)
                return
            
            # Set new status
            activity = discord.Game(name=status_text)
            await self.bot.change_presence(activity=activity, status=discord.Status.online)
            
            success_embed = discord.Embed(
                title="✅ Status Updated",
                description=f"Bot status changed to: **{status_text}**",
                color=MODMAIL_EMBED_COLOR
            )
            success_embed.add_field(name="Changed by", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=success_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Status Error",
                description=f"An error occurred while changing status: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Repair(bot))