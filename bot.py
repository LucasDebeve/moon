import asyncio

import discord
import selenium
from discord.ext import commands
import logging
from pathlib import Path
import os
from dotenv import load_dotenv
import aiosqlite

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DELAY = int(os.getenv("DELAY"))


# The bot alerts the user when a 200 code is returned from a website (verification is made every 5 minutes)
class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=discord.Intents.all(),
            owner_ids=[
                403066350265827330,  # __lucas_d
            ],
            case_insensitive=True,
            slash_commands=True,
            activity=discord.Game(name="!help"),
            status=discord.Status.online,
        )
        # var
        self.footer = "፨ MOON ፨ Made by __lucas_d"
        self.path = str(Path(__file__).parent)
        self.delay = DELAY
        self.database = None

        # Logging
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.WARNING)

        self.log = logging.getLogger()
        self.log.setLevel(logging.DEBUG)

        handler = logging.FileHandler(filename=f"{self.path}/logs/logs.log", encoding="utf-8", mode="w")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        self.log.addHandler(handler)

        handler = logging.FileHandler(filename=f"{self.path}/logs/errors.log", encoding="utf-8", mode="w")
        handler.setLevel(logging.ERROR)
        handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        self.log.addHandler(handler)

        self.log.info("Bot started\n---------------------------------")

    async def setup_hook(self) -> None:
        """
        Setup the bot
        """
        self.database = await aiosqlite.connect("database.db")
        for file in os.listdir(self.path + "/cogs"):
            if file.endswith(".py") and not file.startswith("_"):
                try:
                    await self.load_extension(f"cogs.{file[:-3]}")
                    print(f"Loaded {file[:-3]} cog")
                    self.log.info(f"Loaded {file[:-3]} cog")
                except Exception as e:
                    print(f"Error loading {file[:-3]} cog: {e}")
                    self.log.error(f"Error loading {file[:-3]} cog: {e}")
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        self.log.debug(f"Logged in as {self.user}")
        async with self.database.cursor() as cursor:
            # Create the table if it doesn't exist
            # Config
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS config (server_id INTEGER PRIMARY KEY, channel_id INTEGER, delay INTEGER)")
            # Manga
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS manga (id INTEGER PRIMARY KEY AUTOINCREMENT, title VARCHAR(100), url VARCHAR(255), cover VARCHAR(255))")
            # Chapter
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS chapter (manga_id INTEGER, chapter_num INTEGER, chapter_type CHAR(3), pages INTEGER, release_date DATETIME, PRIMARY KEY (manga_id, chapter_num), FOREIGN KEY (manga_id) REFERENCES manga(id))")
            # ViewOn
            await cursor.execute(
                "CREATE TABLE IF NOT EXISTS viewon (server_id INTEGER, manga_id INTEGER, PRIMARY KEY (server_id, manga_id), FOREIGN KEY (manga_id) REFERENCES manga(id), FOREIGN KEY (server_id) REFERENCES config(server_id))")
        await self.database.commit()


if __name__ == "__main__":
    main_bot = Bot()
    main_bot.run(DISCORD_TOKEN)
