import discord
from discord.ext import commands
import logging
import requests
from bs4 import BeautifulSoup
import asyncio
import os
from dotenv import load_dotenv


load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# The bot alerts the user when a 200 code is returned from a website (verification is made every 5 minutes)
class Bot(discord.client):
    pass