# commands/stock.py

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from config import DAILY_LIMIT, KEY_ROLE_ID
from db import create_db_connection

class Stock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gen", description="Generate an account")
    async def gen(self, interaction: discord.Interaction):
        member = interaction.user

        if not any(role.id == KEY_ROLE_ID for role in member.roles):
            await interaction.response.send_message("You don’t have permission to use this command.", ephemeral=True)
            return

        conn = await create_db_connection()
        cursor = conn.cursor()

        # Check user’s usage for today
        now = datetime.now(timezone.utc)
        cursor.execute(
            "SELECT COUNT(*) FROM logs WHERE user_id = %s AND DATE(timestamp) = CURRENT_DATE;",
            (str(member.id),)
        )
        used_today = cursor.fetchone()[0]

        if used_today >= DAILY_LIMIT:
            await interaction.response.send_message(f"You've reached the daily limit of {DAILY_LIMIT}.", ephemeral=True)
            return

        # Pull available stock
        cursor.execute("SELECT id, content FROM stocks WHERE sold = FALSE LIMIT 1;")
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message("Out of stock right now. Please try later.", ephemeral=True)
            return

        stock_id, account = result

        # Mark as sold
        cursor.execute("UPDATE stocks SET sold = TRUE WHERE id = %s;", (stock_id,))
        cursor.execute(
            "INSERT INTO logs (user_id, content, timestamp) VALUES (%s, %s, %s);",
            (str(member.id), account, now)
        )
        conn.commit()
        cursor.close()
        conn.close()

        await interaction.response.send_message(f"Here’s your account:\n`{account}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Stock(bot))
