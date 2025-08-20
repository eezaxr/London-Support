import discord
from discord.ext import commands
from utils.helpers import is_staff, is_ticket_channel, get_user_from_channel
from config import MODMAIL_EMBED_COLOR, ERROR_EMBED_COLOR

class Claim(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="claim")
    @is_staff()
    @is_ticket_channel()
    async def claim(self, ctx):
        """Claim the current ticket"""
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
            
            # Check if ticket is already claimed
            if hasattr(self.bot, 'claimed_tickets') and channel.id in self.bot.claimed_tickets:
                claimer_id = self.bot.claimed_tickets[channel.id]
                claimer = ctx.guild.get_member(claimer_id)
                claimer_name = claimer.mention if claimer else f"<@{claimer_id}>"
                
                error_embed = discord.Embed(
                    title="❌ Already Claimed",
                    description=f"This ticket is already claimed by {claimer_name}",
                    color=ERROR_EMBED_COLOR
                )
                await ctx.send(embed=error_embed)
                return
            
            # Claim the ticket
            if not hasattr(self.bot, 'claimed_tickets'):
                self.bot.claimed_tickets = {}
            
            self.bot.claimed_tickets[channel.id] = ctx.author.id
            
            # Create claim embed
            claim_embed = discord.Embed(
                title="📌 Ticket Claimed",
                description=f"{ctx.author.mention} has claimed this ticket",
                color=MODMAIL_EMBED_COLOR,
                timestamp=discord.utils.utcnow()
            )
            claim_embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
            claim_embed.add_field(name="Claimed by", value=ctx.author.mention, inline=True)
            claim_embed.set_thumbnail(url=ctx.author.display_avatar.url)
            
            await ctx.send(embed=claim_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while claiming the ticket: {str(e)}",
                color=ERROR_EMBED_COLOR
            )
            await ctx.send(embed=error_embed)

    @commands.command(name="unclaim")
    @is_staff()
    @is_ticket_channel()
    async def unclaim(self, ctx):
        """Unclaim the current ticket"""
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
            
            # Check if ticket is claimed
            if not hasattr(self.bot, 'claimed_tickets') or channel.id not in self.bot.claimed_tickets:
                error_embed = discord.Embed(
                    title="❌ Not Claimed",
                    description="This ticket is not currently claimed.",
                    color=ERROR_EMBED_COLOR
                )
                await ctx.send(embed=error_embed)
                return
            
            claimer_id = self.bot.claimed_tickets[channel.id]
            
            # Check if the person unclaiming is the one who claimed it or has manage_channels permission
            if ctx.author.id != claimer_id and not ctx.author.guild_permissions.manage_channels:
                claimer = ctx.guild.get_member(claimer_id)
                claimer_name = claimer.mention if claimer else f"<@{claimer_id}>"
                
                error_embed = discord.Embed(
                    title="❌ Permission Denied",
                    description=f"Only {claimer_name} or someone with Manage Channels permission can unclaim this ticket.",
                    color=ERROR_EMBED_COLOR
                )
                await ctx.send(embed=error_embed)
                return
            
            # Unclaim the ticket
            claimer = ctx.guild.get_member(claimer_id)
            claimer_name = claimer.display_name if claimer else f"<@{claimer_id}>"
            
            del self.bot.claimed_tickets[channel.id]
            
            # Create unclaim embed
            unclaim_embed = discord.Embed(
                title="📌 Ticket Unclaimed",
                description=f"This ticket has been unclaimed by {ctx.author.mention}",
                color=0xffaa00,  # Orange color
                timestamp=discord.utils.utcnow()
            )
            unclaim_embed.add_field(name="User", value=f"{user} ({user.id})", inline=True)
            unclaim_embed.add_field(name="Previously claimed by", value=claimer_name, inline=True)
            unclaim_embed.add_field(name="Unclaimed by", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=unclaim_embed)
            
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while unclaiming the ticket: {str(e)}",
                color=ERROR_EMBED_COLOR
            )
            await ctx.send(embed=error_embed)

async def setup(bot):
    await bot.add_cog(Claim(bot))