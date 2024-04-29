from datetime import time, datetime

import aiosqlite
import discord
from discord.ext import commands, tasks
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
import asyncio

from bot import Bot


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


class Commands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.check_onepiece.start()

    def cog_unload(self):
        self.check_onepiece.cancel()

    def cog_reload(self):
        self.check_onepiece.cancel()

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

    async def get_last_chapter(self, manga_id: tuple) -> tuple[int, str, int]:
        """
        Get the last chapter number and url of manga from a manga id
        :param manga_id: Manga ID
        :return: Tuple with chapter number and url and number of pages
        """
        async with aiosqlite.connect("database.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute(
                    "SELECT c.chapter_num, m.url, m.cover FROM chapter c JOIN manga m ON c.manga_id = m.id WHERE m.id = ? ORDER BY chapter_num DESC LIMIT 1",
                    manga_id)
                self.bot.log.debug(
                    f"SELECT c.chapter_num, m.url, m.cover FROM chapter c JOIN manga m ON c.manga_id = m.id WHERE m.id = {manga_id} ORDER BY chapter_num DESC LIMIT 1")
                return await cursor.fetchone() or (0, "", 0)

    async def set_last_chapter(self, manga_id: int, chapter_num: int, type_chapter: str, num_pages: int) -> None:
        """
        Set the last chapter number of manga
        :param manga_id: Manga ID
        :param chapter_num: Chapter number
        :param type_chapter: Chapter type
        :param num_pages: Number of pages
        """
        async with self.bot.database.cursor() as cursor:
            maintenant = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            type_du_chapitre = type_chapter[:3].upper()
            await cursor.execute(
                "INSERT INTO chapter (manga_id, chapter_num, chapter_type, pages, release_date) VALUES (?, ?, ?, ?, ?)",
                (manga_id, chapter_num, type_du_chapitre, num_pages, maintenant))
            self.bot.log.debug(
                f"INSERT INTO chapter (manga_id, chapter_num, chapter_type, pages, release_date) VALUES ({manga_id}, {chapter_num}, {type_chapter[:3].upper()}, {num_pages}, {maintenant})")
        await self.bot.database.commit()

    async def getAllFollowedManga(self, guild_id: str):
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT manga_id FROM viewon WHERE server_id = ?", (guild_id, ))
            return await cursor.fetchall()

    async def getChannel(self, guild_id: str):
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT channel_id FROM config WHERE server_id = ?", (guild_id, ))
            return await cursor.fetchone()

    @tasks.loop(seconds=20, reconnect=True)
    async def check_onepiece(self):
        # TODO: Get guild_id from the bot
        guild_id = "716301779096043552"

        # Get all followed manga
        followed_mangas = await self.getAllFollowedManga(guild_id)
        print(f"Followed mangas: {followed_mangas}")
        channel_id = await self.getChannel(guild_id)
        print(f"Channel ID: {channel_id}")
        channel = self.bot.get_channel(channel_id[0])
        for manga_id in followed_mangas:
            print(f"Checking manga {manga_id}")
            last_db_chapter, url, cover_url = await self.get_last_chapter(manga_id)
            print(f"Last chapter: {last_db_chapter}")
            code, driver = await check_website(url + "-" + str(last_db_chapter + 1))
            if code == 200:
                title = driver.find_element(By.CSS_SELECTOR, "h1.entry-title[itemprop=name]").text
                self.bot.log.debug(f"{title} is up")
                print(f"{title} is up")
                embed = discord.Embed(
                    title=title,
                    color=discord.Color.blue(),
                    description=url + "-" + str(last_db_chapter + 1),
                )
                chapter = driver.find_element(By.CSS_SELECTOR, "h1.entry-title[itemprop=name]").text.split(" ")[-1]
                embed.add_field(
                    name="Chapter",
                    value=chapter,
                )
                pages = driver.find_element(By.CSS_SELECTOR, "select#select-paged option:last-child").text.split("/")[
                    -1]
                embed.add_field(
                    name="Pages",
                    value=pages,
                )
                # Detect if (driver.find_element(By.CSS_SELECTOR, "select#selected-paged option[selected]")) contains
                # "RAW"
                type_of_chapter = "Normal"
                if "RAW" in driver.find_element(By.CSS_SELECTOR, "select#chapter option[selected]").text:
                    embed.add_field(
                        name="Mode",
                        value="RAW",
                    )
                    type_of_chapter = "RAW"
                else:
                    if "VUS" in driver.find_element(By.CSS_SELECTOR, "select#chapter option[selected]").text:
                        embed.add_field(
                            name="Mode",
                            value="VUS",
                        )
                        type_of_chapter = "VUS"
                    else:
                        embed.add_field(
                            name="Mode",
                            value="Normal",
                        )
                embed.set_footer(text=self.bot.footer)
                embed.set_thumbnail(url=cover_url)
                embed.set_image(url=driver.find_element(By.CSS_SELECTOR, "#readerarea img:first-child")
                                    .get_attribute("src"))

                await self.set_last_chapter(1, int(chapter), type_of_chapter, int(pages))
                await channel.send(embed=embed)
            elif code == 404:
                print(f"One Piece hasn't released a new chapter yet ({last_db_chapter + 1})")
                self.bot.log.debug(f"One Piece hasn't released a new chapter yet ({last_db_chapter + 1})")

            try:
                driver.quit()
            except Exception as e:
                print(f"Error closing the driver: {e}")
                self.bot.log.error(f"Error closing the driver: {e}")

    @check_onepiece.before_loop
    async def before_check_website(self):
        print("Waiting for bot to be ready")
        await self.bot.wait_until_ready()
        print("Bot is ready")


async def setup(client):
    await client.add_cog(Commands(client))
