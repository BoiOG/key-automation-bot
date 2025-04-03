# main.py

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot instance
bot = commands.Bot(command_prefix="?", intents=intents)

# Load all command modules (cogs)
@bot.event
async def setup_hook():
    await bot.load_extension("commands.claim")
    await bot.load_extension("commands.keygen")
    await bot.load_extension("commands.load_pull")
    await bot.load_extension("commands.logs")
    await bot.load_extension("commands.misc")
    await bot.load_extension("commands.notes")
    await bot.load_extension("commands.order")
    await bot.load_extension("commands.redeemcode")
    await bot.load_extension("commands.replace")
    await bot.load_extension("commands.reward")
    await bot.load_extension("commands.stock")
    await bot.load_extension("commands.util")

# Basic startup log
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user} (ID: {bot.user.id})")

# Run bot
bot.run(TOKEN)
