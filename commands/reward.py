# commands/reward.py

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from config import LOGS_CHANNEL_ID
from db import create_db_connection

class Reward(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reward", description="Redeem your reward key for eligible orders")
    @app_commands.describe(orderid="Your order ID")
    async def reward(self, interaction: discord.Interaction, orderid: str):
        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM reward_keys WHERE sold = FALSE")
        available = cursor.fetchone()[0]

        if available < 1:
            await interaction.response.send_message("We're out of reward keys right now. Please try again later.", ephemeral=True)
            return

        if len(orderid) <= 12:
            return await interaction.response.send_message("Invalid order ID", ephemeral=True)

        cursor.execute("SELECT paid, updated_at FROM orders WHERE slug = %s", (orderid,))
        result = cursor.fetchone()

        if not result:
            return await interaction.response.send_message("Order not found", ephemeral=True)

        paid, updated_at = result

        if not paid:
            return await interaction.response.send_message("This order hasn’t been paid yet.", ephemeral=True)

        updated_at = updated_at.replace(tzinfo=timezone.utc)
        cutoff = datetime(2023, 10, 20, tzinfo=timezone.utc)
        if updated_at < cutoff:
            return await interaction.response.send_message("This order isn’t eligible for a reward (before 10/20).", ephemeral=True)

        cursor.execute("SELECT sold FROM reward_keys WHERE order_id = %s", (orderid,))
        if cursor.fetchone():
            return await interaction.response.send_message("This order has already claimed a reward.", ephemeral=True)

        cursor.execute("SELECT reward_key FROM reward_keys WHERE sold = FALSE LIMIT 1")
        reward_row = cursor.fetchone()

        if not reward_row:
            return await interaction.response.send_message("No reward keys available at the moment.", ephemeral=True)

        key = reward_row[0]
        cursor.execute("UPDATE reward_keys SET sold = TRUE, order_id = %s WHERE reward_key = %s", (orderid, key))
        conn.commit()

        try:
            await interaction.user.send(
                f"🎉 Here is your reward key:\n\n`{key}`\n\n"
                "To redeem:\n"
                "1. Visit the official product redemption page.\n"
                "2. Paste your key into the form.\n"
                "3. Follow any product-specific steps."
            )
        except:
            logs = self.bot.get_channel(LOGS_CHANNEL_ID)
            if logs:
                embed = discord.Embed(
                    title="Failed to send reward via DM",
                    description=f"User: {interaction.user.mention}",
                    color=discord.Color.red()
                )
                embed.add_field(name="Reward Key", value=key)
                await logs.send(embed=embed)

        cursor.close()
        conn.close()

        embed = discord.Embed(
            title="Reward Claimed",
            description=f"User: {interaction.user.mention}\nOrder ID: {orderid}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Key", value=key, inline=False)
        embed.set_footer(text="Reward Log")

        logs = self.bot.get_channel(LOGS_CHANNEL_ID)
        if logs:
            await logs.send(embed=embed)

        await interaction.response.send_message("✅ Reward key sent via DM!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Reward(bot))
