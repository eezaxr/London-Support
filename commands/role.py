import discord
from discord.ext import commands

class RoleCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Specific user ID who can run this command
        self.authorized_user_id = 498952210701352981
        # Channel to send notifications to
        self.notification_channel_id = 1407804143892172810

    def is_authorized_user(self, user_id):
        """Check if user is authorized to run role commands"""
        return user_id == self.authorized_user_id

    @commands.command(name="role")
    async def role_command(self, ctx, member: discord.Member = None, role: discord.Role = None):
        """Add or remove a role from a user. Only usable by authorized user."""
        
        # Check if user is authorized
        if not self.is_authorized_user(ctx.author.id):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return

        # Check if command is used in a guild (not DMs)
        if not ctx.guild:
            embed = discord.Embed(
                title="❌ Invalid Usage",
                description="This command can only be used in a server, not in DMs.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return

        # Check if both member and role were provided
        if not member or not role:
            embed = discord.Embed(
                title="❌ Invalid Usage",
                description="Please provide both a user and a role.\n\n**Usage:** `?role @user @role`",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Examples:",
                value="• `?role @JohnDoe @Moderator`\n• `?role @user123 @VIP`",
                inline=False
            )
            await ctx.send(embed=embed, delete_after=15)
            return

        # Check bot permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            embed = discord.Embed(
                title="❌ Bot Permission Error",
                description="I don't have permission to manage roles in this server.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return

        # Check if the role is higher than the bot's highest role
        if role.position >= ctx.guild.me.top_role.position:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description=f"I cannot manage the role `{role.name}` because it's higher than or equal to my highest role in the hierarchy.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return

        # Check if the role is higher than the author's highest role (for safety)
        if role.position >= ctx.author.top_role.position and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(
                title="❌ Role Hierarchy Error",
                description=f"You cannot manage the role `{role.name}` because it's higher than or equal to your highest role in the hierarchy.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            return

        try:
            # Check if member already has the role
            if role in member.roles:
                # Remove the role
                await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
                embed = discord.Embed(
                    title="✅ Role Removed",
                    description=f"Successfully removed the role `{role.name}` from {member.mention}.",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
                embed.add_field(name="Role", value=f"{role.name}", inline=True)
                embed.add_field(name="Action", value="Removed", inline=True)
            else:
                # Add the role
                await member.add_roles(role, reason=f"Role added by {ctx.author}")
                embed = discord.Embed(
                    title="✅ Role Added",
                    description=f"Successfully added the role `{role.name}` to {member.mention}.",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="User", value=f"{member} ({member.id})", inline=True)
                embed.add_field(name="Role", value=f"{role.name}", inline=True)
                embed.add_field(name="Action", value="Added", inline=True)

            embed.set_footer(text=f"Action performed by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

            # Send notification to the specified channel
            try:
                notification_channel = self.bot.get_channel(self.notification_channel_id)
                if notification_channel:
                    await notification_channel.send(embed=embed)
                else:
                    print(f"⚠️ Could not find notification channel with ID {self.notification_channel_id}")
            except Exception as e:
                print(f"❌ Failed to send notification to channel: {e}")

        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while trying to modify the role: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
        except Exception as e:
            print(f"Unexpected error in role command: {e}")
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An unexpected error occurred. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)

async def setup(bot):
    await bot.add_cog(RoleCommand(bot))