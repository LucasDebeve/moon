from datetime import time

import discord
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import asyncio


async def check_website(url: str) -> tuple[int, webdriver]:
    """
    Get content and status code from a website after javascript execution
    :param url: Website URL
    :return: Tuple with status code and content
    """
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"select#chapter option[selected]"))
        )
    except TimeoutException:
        return 404, None

    return 200, driver


class MyCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user} ({self.bot.user.id})")

    # Command who ping a website
    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context) -> discord.Message:
        embed = discord.Embed(
            title="Pinging...",
            color=discord.Color.blue(),
            description="Pinging the bot to see if it's alive",
        )

        embed.add_field(
            name="Latency",
            value="Loading...",
        )

        embed.set_field_at(
            index=0,
            name="Latency",
            value=f"{round(self.bot.latency * 1000)}ms",
        )

        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=self.bot.footer)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        return await ctx.send(embed=embed)

    @commands.command(name="onepiece")
    async def onepiece(self, ctx: commands.Context, *args) -> discord.Message:
        embed = discord.Embed(
            title="One Piece",
            color=discord.Color.blue(),
            description=""
        )

        url = "https://www.lelmanga.com/one-piece-" + "-".join(args)
        code, driver = await check_website(url)

        if code == 200:
            embed.add_field(
                name="Status",
                value="Online",
            )
            embed.add_field(
                name="Chapter",
                value="Loading...",
            )

            # Scrap the content of selct#chapter option[selected]
            chapter = driver.find_element(By.CSS_SELECTOR, "select#chapter option[selected]").text

            embed.set_field_at(
                index=1,
                name="Chapter",
                value="Chapter " + chapter,
            )
        else:
            embed.add_field(
                name="Status",
                value="Offline",
            )

        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=self.bot.footer)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        return await ctx.send(embed=embed)

