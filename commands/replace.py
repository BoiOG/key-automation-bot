# commands/replace.py

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from config import ADMIN_ROLE_ID, SUPPORT_ROLE_ID, LOGS_CHANNEL_ID
from db import create_db_connection

class Replace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, member: discord.Member):
        return any(role.id == ADMIN_ROLE_ID for role in member.roles)

    def is_support(self, member: discord.Member):
        return any(role.id == SUPPORT_ROLE_ID for role in member.roles)

    async def perform_replacement(self, ctx, num, order_id, note):
        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT product_id FROM orders WHERE slug = %s", (order_id,))
        result_productid = cursor.fetchone()
        if not result_productid:
            await ctx.send("Invalid Order ID.")
            return

        cursor.execute("SELECT COUNT(*) FROM stocks WHERE product_id = %s AND sold = FALSE", (result_productid[0],))
        num_available = cursor.fetchone()[0]
        if num_available < num:
            await ctx.send("Not enough stock available.")
            return

        cursor.execute(
            "SELECT id, content FROM stocks WHERE product_id = %s AND sold = FALSE LIMIT %s",
            (result_productid[0], num)
        )
        replacements = cursor.fetchall()

        accounts = "\n\n".join([acc[1] for acc in replacements])
        embed = discord.Embed(
            title="Replacement",
            url=f"https://example.com/order/{order_id}",
            description=accounts,
            color=0x26e36f
        )
        embed.add_field(name="Order ID", value=order_id)
        embed.set_footer(text="Your order page has been updated.")
        await ctx.send(embed=embed)

        cursor.execute("SELECT content FROM orders WHERE slug = %s", (order_id,))
        content = cursor.fetchone()[0]
        content += f"\nREPLACEMENT:{accounts}"
        cursor.execute("UPDATE orders SET content = %s WHERE slug = %s", (content, order_id))

        for acc in replacements:
            cursor.execute("UPDATE stocks SET sold = TRUE WHERE id = %s", (acc[0],))

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        author = ctx.author.name

        cursor.execute("SELECT notes FROM replacement_notes WHERE order_id = %s", (order_id,))
        existing = cursor.fetchone()
        if existing:
            updated = f'{existing[0]}\n\n"{note}" by {author} | Replaced {num} on {now}'
            cursor.execute("UPDATE replacement_notes SET notes = %s WHERE order_id = %s", (updated, order_id))
        else:
            cursor.execute(
                "INSERT INTO replacement_notes (order_id, notes) VALUES (%s, %s)",
                (order_id, f'"{note}" by {author} | Replaced {num} on {now}')
            )

        conn.commit()
        cursor.close()
        conn.close()

    @app_commands.command(name="replace", description="Submit a replacement request")
    @app_commands.describe(num="How many accounts to replace", order_id="Order ID", note="Reason for replacement")
    async def replace(self, interaction: discord.Interaction, num: int, order_id: str, note: str):
        member = interaction.user
        logs_channel = self.bot.get_channel(LOGS_CHANNEL_ID)

        if self.is_admin(member):
            await self.perform_replacement(interaction, num, order_id, note)
            return

        elif self.is_support(member):
            await interaction.response.send_message("Waiting for admin approval...", ephemeral=True)

            embed = discord.Embed(title="Replacement Request", color=0xe74c3c)
            embed.add_field(name="Staff", value=member.mention)
            embed.add_field(name="Order ID", value=order_id)
            embed.add_field(name="Note", value=note)
            embed.add_field(name="Amount", value=str(num))
            embed.set_footer(text="React with ✅ to approve or ❌ to deny.")

            msg = await logs_channel.send(embed=embed)
            await logs_channel.send(f"<@&{ADMIN_ROLE_ID}>")
            await msg.add_reaction("✅")
            await msg.add_reaction("❌")

            def check(reaction, user):
                return (
                    user != self.bot.user
                    and str(reaction.emoji) in ["✅", "❌"]
                    and reaction.message.id == msg.id
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=None)
            except Exception as e:
                await interaction.followup.send(f"Approval failed: {e}")
                return

            if str(reaction.emoji) == "✅":
                await interaction.followup.send("Approved by admin.", ephemeral=True)
                await self.perform_replacement(interaction, num, order_id, note)
                await logs_channel.send("Replacement approved ✅")
            else:
                await logs_channel.send("Replacement denied ❌")
                await interaction.followup.send("Denied by admin.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Replace(bot))
