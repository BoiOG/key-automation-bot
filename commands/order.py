# commands/order.py

import discord
from discord.ext import commands
from discord import app_commands
from config import LOGS_CHANNEL_ID
from db import create_db_connection

class OrderInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="order", description="Look up order info by Order ID")
    @app_commands.describe(order_id="The order ID to search")
    async def order_info(self, interaction: discord.Interaction, order_id: str):
        member = interaction.user
        guild = interaction.guild
        logs_channel = self.bot.get_channel(LOGS_CHANNEL_ID)

        # Require user to have a staff role
        staff_role = discord.utils.get(guild.roles, name="Staff")
        if not staff_role or staff_role not in member.roles:
            embed = discord.Embed(
                title="Command Attempt",
                description=f"{member.mention} tried to use `/order` without permission.",
                color=discord.Color.red()
            )
            if logs_channel:
                await logs_channel.send(embed=embed)
            await interaction.response.send_message("You don’t have permission to use this command.", ephemeral=True)
            return

        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM orders WHERE slug = %s", (order_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            await interaction.response.send_message("Invalid Order ID.", ephemeral=True)
            return

        cursor.execute(
            "SELECT content, email, slug, created_at, paid FROM orders WHERE slug = %s",
            (order_id,)
        )
        order = cursor.fetchone()
        cursor.close()
        conn.close()

        if not order:
            await interaction.response.send_message("Order not found.", ephemeral=True)
            return

        content, email, slug, created_at, paid = order

        if not paid or '@' not in content or '@' not in email:
            await interaction.response.send_message("Unpaid or invalid order.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Order Information",
            url=f"https://example.com/order/{order_id}",
            color=0x26e36f
        )
        embed.add_field(name="Account", value=content, inline=False)
        embed.add_field(name="Email", value=email, inline=False)
        embed.add_field(name="Order ID", value=slug)
        embed.add_field(name="Created At", value=str(created_at))

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(OrderInfo(bot))
