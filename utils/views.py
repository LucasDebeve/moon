import aiosqlite
import discord


class MangaModal(discord.ui.Modal, title="Entre le manga à suivre"):
    manga_title = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Titre",
        max_length=100,
        required=True,
        placeholder="Titre du manga"
    )

    manga_url = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="URL",
        max_length=255,
        required=True,
        placeholder="www.lelmanga.com"
    )
    manga_cover = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Cover",
        max_length=255,
        required=False,
        placeholder="URL de la couverture"
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        # Add the manga to the database if it doesn't exist
        async with aiosqlite.connect("database.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute("SELECT * FROM manga WHERE url = ? AND title LIKE ? ",
                                     (self.manga_url.value, self.manga_title.value))
                if not await cursor.fetchone():
                    await cursor.execute("INSERT INTO manga (title, url, cover) VALUES (?, ?, ?)",
                                         (self.manga_title.value, self.manga_url.value, self.manga_cover.value))
                    await db.commit()

    async def on_error(self, interaction: discord.Interaction, error) -> None:
        print(f"An error occurred while Modal: {error}")


class ConfigMenu(discord.ui.View):
    def __init__(self, channels: list[discord.TextChannel], **kwargs):
        super().__init__(**kwargs)


    async def on_timeout(self):
        await self.message.edit(view=None)

    async def on_error(self, error: Exception) -> None:
        print(f"An error occurred while ConfigMenu: {error}")