import discord
from discord.ext import commands
from utils.helpers import is_staff, is_ticket_channel, get_user_from_channel, send_dm_safely
from config import MODMAIL_EMBED_COLOR, ERROR_EMBED_COLOR

class Reply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reply")
    @is_staff()
    @is_ticket_channel()
    async def reply(self, ctx, *, message: str):
        """Reply to the user in this ticket"""
        try:
            channel = ctx.channel
            user = await get_user_from_channel(self.bot, channel)
            
            if not user:
                error_embed = discord.Embed(
                    title="❌ Error",
                    description="Could not find the user for this ticket.",
                    color=ERROR_EMBED_COLOR
                )
                await ctx.send(embed=error_embed)
                return
            
            # Create embed for user DM
            user_embed = discord.Embed(
                description=message,
                color=MODMAIL_EMBED_COLOR,
                timestamp=discord.utils.utcnow()
            )
            user_embed.set_author(
                name=f"{ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            
            # Send to user
            dm_sent = await send_dm_safely(user, embed=user_embed)
            
            # Create confirmation embed for ticket channel
            if dm_sent:
                confirmation_embed = discord.Embed(
                    title="✅ Reply Sent",
                    description=f"Successfully sent reply to {user.mention}",
                    color=MODMAIL_EMBED_COLOR
                )
                confirmation_embed.add_field(name="Message", value=message, inline=False)
                confirmation_embed.add_field(name="Sent by", value=ctx.author.mention, inline=True)
            else:
                confirmation_embed = discord.Embed(
                    title="❌ Reply Failed",
                    description=f"Could not send reply to {user.mention} (DMs may be disabled)",
                    color=ERROR_EMBED_COLOR
                )
                confirmation_embed.add_field(name="Attempted Message", value=message, inline=False)
            
            await ctx.send(embed=confirmation_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while sending the reply: {str(e)}",
                color=ERROR_EMBED_COLOR
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="a_reply")
    @is_staff()
    @is_ticket_channel()
    async def a_reply(self, ctx, *, message: str):
        """Send an anonymous reply to the user"""
        try:
            channel = ctx.channel
            user = await get_user_from_channel(self.bot, channel)
            
            if not user:
                error_embed = discord.Embed(
                    title="❌ Error",
                    description="Could not find the user for this ticket.",
                    color=ERROR_EMBED_COLOR
                )
                await ctx.send(embed=error_embed)
                return
            
            # Create anonymous embed for user DM
            user_embed = discord.Embed(
                description=message,
                color=MODMAIL_EMBED_COLOR,
                timestamp=discord.utils.utcnow()
            )
            user_embed.set_author(
                name="Staff",
                icon_url=ctx.guild.icon.url if ctx.guild.icon else None
            )
            
            # Send to user
            dm_sent = await send_dm_safely(user, embed=user_embed)
            
            # Create confirmation embed for ticket channel
            if dm_sent:
                confirmation_embed = discord.Embed(
                    title="✅ Anonymous Reply Sent",
                    description=f"Successfully sent anonymous reply to {user.mention}",
                    color=MODMAIL_EMBED_COLOR
                )
                confirmation_embed.add_field(name="Message", value=message, inline=False)
                confirmation_embed.add_field(name="Sent by", value=ctx.author.mention, inline=True)
                confirmation_embed.add_field(name="Anonymous", value="Yes", inline=True)
            else:
                confirmation_embed = discord.Embed(
                    title="❌ Anonymous Reply Failed",
                    description=f"Could not send reply to {user.mention} (DMs may be disabled)",
                    color=ERROR_EMBED_COLOR
                )
                confirmation_embed.add_field(name="Attempted Message", value=message, inline=False)
            
            await ctx.send(embed=confirmation_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while sending the anonymous reply: {str(e)}",
                color=ERROR_EMBED_COLOR
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Reply(bot))