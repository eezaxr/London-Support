import discord
from discord.ext import commands
import asyncio
from utils.helpers import is_staff, is_ticket_channel, get_user_from_channel, create_transcript, send_dm_safely
from config import TRANSCRIPT_CHANNEL, MODMAIL_EMBED_COLOR, ERROR_EMBED_COLOR

class Close(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="close")
    @is_staff()
    @is_ticket_channel()
    async def close(self, ctx, *, reason: str = "No reason provided"):
        """Close the current ticket"""
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
            
            # Create closing embed for ticket channel
            embed = discord.Embed(
                title="🔒 Ticket Closing",
                description=f"Ticket is being closed by {ctx.author.mention}",
                color=MODMAIL_EMBED_COLOR
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Closed by", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            # Create transcript
            transcript_file = await create_transcript(channel)
            
            # Send transcript to transcript channel
            transcript_channel = self.bot.get_channel(TRANSCRIPT_CHANNEL)
            if transcript_channel:
                transcript_embed = discord.Embed(
                    title="📄 Ticket Transcript",
                    description=f"Transcript for ticket with {user} ({user.id})",
                    color=MODMAIL_EMBED_COLOR
                )
                transcript_embed.add_field(name="Closed by", value=ctx.author.mention, inline=True)
                transcript_embed.add_field(name="Reason", value=reason, inline=True)
                transcript_embed.add_field(name="User", value=f"{user} ({user.id})", inline=False)
                
                await transcript_channel.send(embed=transcript_embed, file=transcript_file)
            
            # Notify user
            user_embed = discord.Embed(
                title="🔒 Ticket Closed",
                description="Your modmail ticket has been closed.",
                color=MODMAIL_EMBED_COLOR
            )
            user_embed.add_field(name="Reason", value=reason, inline=False)
            user_embed.add_field(
                name="Need more help?", 
                value="Feel free to send another message to create a new ticket.", 
                inline=False
            )
            
            dm_sent = await send_dm_safely(user, embed=user_embed)
            if not dm_sent:
                await channel.send("⚠️ Could not send closing notification to user (DMs disabled)")
            
            # Remove from active tickets and claimed tickets
            if hasattr(self.bot, 'active_tickets') and user.id in self.bot.active_tickets:
                del self.bot.active_tickets[user.id]
            
            if hasattr(self.bot, 'claimed_tickets') and channel.id in self.bot.claimed_tickets:
                del self.bot.claimed_tickets[channel.id]
            
            # Delete channel after 5 seconds
            await channel.send("This channel will be deleted in 5 seconds...")
            await asyncio.sleep(5)
            await channel.delete()
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while closing the ticket: {str(e)}",
                color=ERROR_EMBED_COLOR
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Close(bot))