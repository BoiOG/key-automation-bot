# commands/keygen.py

import discord
from discord.ext import commands
from discord import app_commands
from config import SUPPORT_ROLE_ID, TRIAL_SUPPORT_ROLE_ID, ADMIN_ROLE_ID
from db import create_db_connection
from datetime import datetime, timezone

class KeyGen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_permission(self, member: discord.Member):
        return any(role.id in [SUPPORT_ROLE_ID, TRIAL_SUPPORT_ROLE_ID, ADMIN_ROLE_ID] for role in member.roles)

    @app_commands.command(name="sendstock", description="Manually send an account to a user")
    @app_commands.describe(user="The user to receive the account")
    async def sendstock(self, interaction: discord.Interaction, user: discord.User):
        member = interaction.user

        if not self.has_permission(member):
            await interaction.response.send_message("You don’t have permission to use this command.", ephemeral=True)
            return

        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, content FROM stocks WHERE sold = FALSE LIMIT 1;")
        result = cursor.fetchone()

        if not result:
            await interaction.response.send_message("No stock available to send.", ephemeral=True)
            return

        stock_id, account = result

        # Mark it sold + log it
        cursor.execute("UPDATE stocks SET sold = TRUE WHERE id = %s;", (stock_id,))
        cursor.execute(
            "INSERT INTO logs (user_id, content, timestamp) VALUES (%s, %s, %s);",
            (str(user.id), account, datetime.now(timezone.utc))
        )
        conn.commit()
        cursor.close()
        conn.close()

        try:
            await user.send(f"You've received an account:\n`{account}`")
            await interaction.response.send_message("Account sent via DM.", ephemeral=True)
        except:
            await interaction.response.send_message("Failed to DM the user.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(KeyGen(bot))
