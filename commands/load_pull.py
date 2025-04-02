# commands/load_pull.py

import discord
from discord.ext import commands
from config import LOGS_CHANNEL_ID
from db import create_db_connection

AUTHORIZED_IDS = [1108152698509270794, 299466333435643654]

class KeyManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="loadkeys", description="Load product keys into the database")
    async def loadkeys(self, ctx: commands.Context, *keys: str):
        if ctx.author.id not in AUTHORIZED_IDS:
            await self.log_attempt(ctx)
            return await ctx.reply("You don’t have permission to run this command.", mention_author=True)

        if not keys:
            return await ctx.reply("Please provide keys to load.", ephemeral=True)

        conn = await create_db_connection()
        cursor = conn.cursor()

        for key in keys:
            cursor.execute("INSERT INTO codes (game_code) VALUES (%s)", (key,))
            cursor.execute(
                "INSERT INTO stocks (content, product_id, user_id, sold) VALUES (%s, %s, %s, %s)",
                ("Join our platform and use /redeemkey to claim your code.", 28, 4, False)
            )

        conn.commit()
        cursor.close()
        conn.close()
        await ctx.reply(f"{len(keys)} keys loaded into the system.", ephemeral=True)

    @commands.command(name="pullkeys", description="Pull available keys from the system")
    async def pullkeys(self, ctx: commands.Context, amount: int):
        if ctx.author.id not in AUTHORIZED_IDS:
            await self.log_attempt(ctx)
            return await ctx.reply("You don’t have permission to run this command.", mention_author=True)

        conn = await create_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT game_code FROM codes WHERE sold = FALSE LIMIT %s", (amount,))
        available = cursor.fetchall()

        if not available:
            return await ctx.reply("No unsold keys found.", ephemeral=True)

        for key in available:
            cursor.execute("UPDATE codes SET sold = TRUE WHERE game_code = %s", (key[0],))
            cursor.execute("UPDATE stocks SET sold = TRUE WHERE product_id = %s AND sold = FALSE LIMIT 1", (28,))

        conn.commit()
        cursor.close()
        conn.close()

        code_list = "\n".join(key[0] for key in available)
        await ctx.reply(f"🔑 Pulled {amount} key(s):\n\n{code_list}", ephemeral=True)

    async def log_attempt(self, ctx):
        logs = self.bot.get_channel(LOGS_CHANNEL_ID)
        embed = discord.Embed(
            title="Unauthorized Attempt",
            description=f"{ctx.author.mention} tried to use `{ctx.command}`.",
            color=discord.Color.red()
        )
        if logs:
            await logs.send(embed=embed)

async def setup(bot):
    await bot.add_cog(KeyManagement(bot))
