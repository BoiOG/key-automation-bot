# commands/util.py

import discord
from discord.ext import commands
from config import LOGS_CHANNEL_ID

AUTHORIZED_IDS = [1108257698509770794, 899464333455683604]
CARD_IMAGE_URL = 'https://i.imgur.com/FPUWpsH.png'

# Embed helper
def create_embed(title: str = "", description: str = "", color: int = 0x2F3136) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shutdown")
    async def shutdown(self, ctx):
        if ctx.author.id not in AUTHORIZED_IDS:
            await self.log_attempt(ctx)
            return await ctx.reply("You don’t have permission to run this command.", mention_author=True)
        await ctx.send("Shutting down...")
        await ctx.bot.close()

    @commands.command(name="card")
    async def card_disclaimer(self, ctx):
        if ctx.author.id not in AUTHORIZED_IDS:
            await self.log_attempt(ctx)
            return await ctx.reply("You don’t have permission to run this command.", mention_author=True)

        embed = create_embed(
            title="Card Disclaimer",
            description="Reminder of our terms displayed during checkout.",
            color=discord.Color.blue()
        )
        embed.set_image(url=CARD_IMAGE_URL)
        await ctx.send(embed=embed)

        async for message in ctx.channel.history(limit=None, oldest_first=True):
            if not message.author.bot:
                await ctx.send(message.author.mention)
                break

    @commands.command(name="i")
    async def instructions(self, ctx):
        if ctx.author.id not in AUTHORIZED_IDS:
            await self.log_attempt(ctx)
            return await ctx.reply("You don’t have permission to run this command.", mention_author=True)

        embed = create_embed(
            title="Order Info Form",
            description="Please provide the following info so we can help:",
            color=discord.Color.green()
        )
        embed.add_field(name="1) Email used at checkout", value="e.g. `you@example.com`", inline=False)
        embed.add_field(name="2) Product name or type", value="e.g. `Trial`, `Pro`, `Subscription`", inline=False)
        await ctx.send(embed=embed)

    async def log_attempt(self, ctx):
        logs = self.bot.get_channel(LOGS_CHANNEL_ID)
        embed = create_embed(
            title="Unauthorized Attempt",
            description=f"{ctx.author.mention} tried to use `{ctx.command}`.",
            color=discord.Color.red()
        )
        if logs:
            await logs.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utility(bot))
