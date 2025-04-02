# commands/logs.py

import discord
from discord.ext import commands
from discord import app_commands
from config import SUPPORT_ROLE_ID, TRIAL_SUPPORT_ROLE_ID, ADMIN_ROLE_ID
from db import create_db_connection

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_permission(self, member: discord.Member):
        return any(role.id in [SUPPORT_ROLE_ID, TRIAL_SUPPORT_ROLE_ID, ADMIN_ROLE_ID] for role in member.roles)

    @app_commands.command(name="viewlogs", description="View recent generation logs")
    @app_commands.describe(limit="How many entries to fetch (max 10)")
    async def viewlogs(self, interaction: discord.Interaction, limit: int = 5):
        member = interaction.user

        if not self.has_permission(member):
            await interaction.response.send_message("You don’t have permission to use this command.", ephemeral=True)
            return

        limit = min(limit, 10)

        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id, content, timestamp FROM logs ORDER BY timestamp DESC LIMIT %s;",
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if not rows:
            await interaction.response.send_message("No logs found.", ephemeral=True)
            return

        embed = discord.Embed(title="Recent Logs", color=0x2F3136)

        for user_id, content, timestamp in rows:
            embed.add_field(
                name=f"User: {user_id}",
                value=f"`{content}`\n<t:{int(timestamp.timestamp())}:R>",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Logs(bot))
