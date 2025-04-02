# commands/claim.py

import discord
from discord.ext import commands
from discord import app_commands
from config import GUILD_ID
from db import create_db_connection

ROLE_NAME = "Customer"

class Claim(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="claim", description="Claim your customer role by providing your order ID")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    @app_commands.describe(orderid="Your order ID from checkout")
    async def claim(self, interaction: discord.Interaction, orderid: str):
        if not ('-' in orderid or '_' in orderid):
            await interaction.response.send_message("Invalid Order ID format.", ephemeral=True)
            return

        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM claimed_orderids WHERE order_id = %s", (orderid,))
        if cursor.fetchone():
            await interaction.response.send_message("This order ID was already claimed.", ephemeral=True)
            cursor.close()
            conn.close()
            return

        cursor.execute("SELECT * FROM orders WHERE slug = %s AND paid = TRUE", (orderid,))
        if not cursor.fetchone():
            await interaction.response.send_message("Order not found or not paid.", ephemeral=True)
            cursor.close()
            conn.close()
            return

        role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
        if role:
            await interaction.user.add_roles(role)

        cursor.execute(
            "INSERT INTO claimed_orderids (order_id, user_id) VALUES (%s, %s)",
            (orderid, interaction.user.id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        await interaction.response.send_message(
            f"✅ You’ve successfully claimed your `{ROLE_NAME}` role, {interaction.user.mention}!",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Claim(bot))
