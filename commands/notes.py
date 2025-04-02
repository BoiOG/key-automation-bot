# commands/notes.py

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from config import ADMIN_ROLE_ID
from db import create_db_connection

class Notes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, member: discord.Member):
        return any(role.id == ADMIN_ROLE_ID for role in member.roles)

    @app_commands.command(name="note", description="Add a note to an order ID")
    @app_commands.describe(order_id="The order ID", message="The note to add")
    async def add_note(self, interaction: discord.Interaction, order_id: str, message: str):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_name = interaction.user.name

        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT notes FROM replacement_notes WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()

        if result:
            new_notes = f'{result[0]}\n\n"{message}" by {user_name} | on {now}'
            cursor.execute("UPDATE replacement_notes SET notes = %s WHERE order_id = %s", (new_notes, order_id))
        else:
            cursor.execute(
                "INSERT INTO replacement_notes (order_id, notes) VALUES (%s, %s)",
                (order_id, f'"{message}" by {user_name} | on {now}')
            )

        conn.commit()
        cursor.close()
        conn.close()

        await interaction.response.send_message("Note added successfully.", ephemeral=True)

    @app_commands.command(name="notes", description="View notes under an order ID")
    @app_commands.describe(order_id="The order ID to check")
    async def get_note(self, interaction: discord.Interaction, order_id: str):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT notes FROM replacement_notes WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            await interaction.response.send_message("No notes found for that order ID.", ephemeral=True)
            return

        notes = result[0]
        embed = discord.Embed(title="Replacement Notes", color=0x26e36f)
        embed.add_field(name="Notes", value=f"**\n{notes}**", inline=False)
        embed.add_field(name="Order ID", value=order_id)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Notes(bot))
