# commands/redeemcode.py

import discord
from discord.ext import commands
from discord import app_commands
from config import LOGS_CHANNEL_ID
from db import create_db_connection

ROLE_NAME = "Customer"

class RedeemKey(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="redeemkey", description="Redeem your purchased product key")
    @app_commands.describe(orderid="Your order ID")
    async def redeemkey(self, interaction: discord.Interaction, orderid: str):
        if len(orderid) <= 12:
            return await interaction.response.send_message("This is an invalid order ID", ephemeral=True)

        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT paid, amount, product_id FROM orders WHERE slug = %s", (orderid,))
        result = cursor.fetchone()

        if not result:
            return await interaction.response.send_message("Order not found", ephemeral=True)

        paid, amount, product_id = result
        if not paid:
            return await interaction.response.send_message("This order has not been paid", ephemeral=True)

        # Prevent double redemption
        cursor.execute("SELECT sold FROM codes WHERE order_id = %s", (orderid,))
        if cursor.fetchone():
            return await interaction.response.send_message("This order has already been used.", ephemeral=True)

        # Pull keys
        cursor.execute("SELECT game_code FROM codes WHERE sold = FALSE LIMIT %s", (amount,))
        available_codes = cursor.fetchall()

        if not available_codes:
            return await interaction.response.send_message("No available product keys at the moment.", ephemeral=True)

        redeemed_keys = [code[0] for code in available_codes]
        for key in redeemed_keys:
            cursor.execute("UPDATE codes SET sold = TRUE, order_id = %s WHERE game_code = %s", (orderid, key))

        conn.commit()

        # Message user
        user = interaction.user
        message = f"🎁 **Here are your product key(s):**\n\n" + "\n".join(redeemed_keys)
        message += "\n\n📝 **Instructions to redeem:**\n"
        message += "1. Visit the official redemption page for your product\n"
        message += "2. Paste your key into the activation form\n"
        message += "3. If required, follow any region or network instructions\n"
        message += "\nThank you for your purchase!"

        try:
            await user.send(message)
        except:
            logs = self.bot.get_channel(LOGS_CHANNEL_ID)
            if logs:
                embed = discord.Embed(title="Failed to DM user", description=user.mention, color=0xFF0000)
                embed.add_field(name="Keys", value="\n".join(redeemed_keys), inline=False)
                await logs.send(embed=embed)

        # Give role + log redemption
        try:
            role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
            if role:
                await user.add_roles(role)
            cursor.execute("INSERT INTO claimed_orderids (order_id, user_id) VALUES (%s, %s)", (orderid, user.id))
            conn.commit()
        except Exception as e:
            print(f"Failed to assign role: {e}")

        cursor.close()
        conn.close()

        embed = discord.Embed(
            title="Key Redemption Logged",
            description=f"User: {user.mention}\nOrder ID: {orderid}",
            color=discord.Color.green()
        )
        embed.add_field(name="Redeemed Keys", value="\n".join(redeemed_keys))
        embed.set_footer(text="Redemption Log")

        logs = self.bot.get_channel(LOGS_CHANNEL_ID)
        if logs:
            await logs.send(embed=embed)

        await interaction.response.send_message("✅ Your product keys and instructions were sent via DM.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RedeemKey(bot))
