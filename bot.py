import asyncio

import discord
from discord.ext import commands
import logging
import requests
from pathlib import Path
import os
from dotenv import load_dotenv
from selenium.webdriver.common.by import By

from myCommands import MyCommands, check_website

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
            activity=discord.Game(name="!help"),
            status=discord.Status.online,
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

        # var
        self.footer = "፨ MOON ፨ Made by __lucas_d"
        self.path = str(Path(__file__).parent)

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
        await self.add_cog(MyCommands(self))
        self.bg_task = self.loop.create_task(self.check_website())
        await self.tree.sync()

    async def check_website(self) -> None:
        await self.wait_until_ready()
        while not self.is_closed():
            await self.check_onepiece()
            await asyncio.sleep(DELAY)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        self.log.debug(f"Logged in as {self.user}")

    async def check_onepiece(self):
        code, driver = await check_website("https://www.lelmanga.com/one-piece-1113")
        embed = discord.Embed(
            title="One Piece",
            color=discord.Color.red(),
            description="One Piece is down",
        )
        channel = self.get_channel(1233080956907159694)
        if code == 200:
            print("One Piece is up")
            self.log.debug("One Piece is up")
            embed = discord.Embed(
                title=driver.find_element(By.CSS_SELECTOR, "h1.entry-title[itemprop=name]").text,
                color=discord.Color.blue(),
                description="One Piece is up",
            )

            embed.add_field(
                name="Chapter",
                value=driver.find_element(By.CSS_SELECTOR, "h1.entry-title[itemprop=name]").text.split(" ")[-1],
            )
            embed.add_field(
                name="Pages",
                value=driver.find_element(By.CSS_SELECTOR, "select#selected-paged option[selected]").text.split("/")[-1],
            )
            # Detect if (driver.find_element(By.CSS_SELECTOR, "select#selected-paged option[selected]")) contains "RAW"
            if "RAW" in driver.find_element(By.CSS_SELECTOR, "select#chapter option[selected]").text:
                embed.add_field(
                    name="Mode",
                    value="RAW",
                )
            else:
                embed.add_field(
                    name="Mode",
                    value="Normal",
                )
            await channel.send(embed=embed)
        elif code == 404:
            print("One Piece is down")
            self.log.debug("One Piece is down")

        driver.quit()



bot = Bot()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
