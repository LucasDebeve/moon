import discord
from discord.ext import commands
from discord import app_commands

from bot import Bot
from utils.views import MangaModal, ConfigMenu


# Slash commands
class Slash(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @app_commands.command(name="manga", description="Entre le manga à suivre")
    async def manga(
            self,
            interaction: discord.Interaction
    ) -> None:
        view = MangaModal()
        view.user = interaction.user
        await interaction.response.send_modal(view)

    @app_commands.command(name="config", description="Configure le suivi d'un manga")
    @app_commands.describe(channel="Le channel où envoyer les notifications",
                           delay="L'intervalle en minutes entre chaque vérification")
    @app_commands.default_permissions(manage_channels=True)
    async def configure(self, interaction: discord.Interaction, channel: discord.TextChannel, delay: int):
        # Add the configuration to the database
        # Server ID, Channel ID, Delay
        async with self.bot.database.cursor() as cursor:
            # Check if the configuration already exists
            guild_id = str(interaction.guild.id)
            await cursor.execute("SELECT * FROM config WHERE server_id = ?", (guild_id, ))
            channel_id = str(channel.id)
            if await cursor.fetchone():
                print("Updating config")
                await cursor.execute("UPDATE config SET channel_id = ?, delay = ? WHERE server_id = ?",
                                     (channel_id, str(delay), guild_id))
            else:
                print("Inserting config")
                await cursor.execute("INSERT INTO config (server_id, channel_id, delay) VALUES (?, ?, ?)",
                                     (guild_id, channel_id, delay))
            await self.bot.database.commit()

        await interaction.response.send_message(
            f"Le suivi de mangas a été configuré pour le channel {channel.mention} avec un délai de {round(delay/60)} minutes")


    @app_commands.command(name="config_manga", description="Configure le suivi d'un manga")
    @app_commands.describe(titre="Le titre du manga", url="L'url du manga", cover="L'url de la couverture")
    @app_commands.default_permissions(manage_channels=True)
    async def configure_manga(self, interaction: discord.Interaction, titre: str, url: str, cover: str):
        # Add the manga to the database if it doesn't exist
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT id FROM manga WHERE url = ? AND lower(title) LIKE ? ",
                                 (url, f"%{titre.lower()}%"))
            manga_id = await cursor.fetchone()
            manga_id = manga_id[0] if manga_id else None
            print(manga_id)
            if not manga_id:
                await cursor.execute("INSERT INTO manga (title, url, cover) VALUES (?, ?, ?)",
                                     (titre, url, cover))
                await self.bot.database.commit()
                manga_id = cursor.lastrowid

            # Add ViewOn to the database
            guild_id = str(interaction.guild.id)

            await cursor.execute("SELECT * FROM viewon WHERE server_id = ? AND manga_id = ?", (guild_id, manga_id))
            if not await cursor.fetchone():
                await cursor.execute("INSERT INTO viewon (server_id, manga_id) VALUES (?, ?)",
                                     (guild_id, manga_id))
                await self.bot.database.commit()

        await interaction.response.send_message(
            f"Le manga {titre} a été ajouté à la liste de suivi")

    @configure_manga.autocomplete("titre")
    async def configure_manga_autocomplete(self, interaction: discord.Interaction, titre: str):
        results = []
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT title FROM manga WHERE lower(title) LIKE ?", (f"%{titre}%",))
            results = await cursor.fetchall()
        return [app_commands.Choice(name=result[0], value=result[0]) for result in results]

    @configure_manga.autocomplete("url")
    async def configure_manga_autocomplete(self, interaction: discord.Interaction, url: str):
        results = []
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT url FROM manga WHERE lower(url) LIKE ?", (f"%{url}%",))
            results = await cursor.fetchall()
            print(results)
        return [app_commands.Choice(name=result[0], value=result[0]) for result in results]

    @configure_manga.autocomplete("cover")
    async def configure_manga_autocomplete(self, interaction: discord.Interaction, cover: str):
        results = []
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT IFNULL(cover, '') FROM manga WHERE lower(cover) LIKE ?", (f"%{cover}%",))
            results = await cursor.fetchall()
        return [app_commands.Choice(name=result[0], value=result[0]) for result in results]

    @app_commands.command(name="list", description="Affiche la liste des mangas suivis")
    async def list_manga(self, interaction: discord.Interaction):
        async with self.bot.database.cursor() as cursor:
            guild_id = str(interaction.guild.id)
            await cursor.execute("SELECT m.title, m.url, m.cover FROM manga m JOIN viewon v ON m.id = v.manga_id WHERE v.server_id = ?", (guild_id,))
            mangas = await cursor.fetchall()

        embed = discord.Embed(
            title="Liste des mangas suivis",
            color=discord.Color.blue()
        )

        for manga in mangas:
            embed.add_field(
                name=manga[0],
                value=f"[Lien]({manga[1]})",
                inline=False
            )
            if manga[2]:
                embed.set_thumbnail(url=manga[2])

        embed.set_footer(text=self.bot.footer)

        await interaction.response.send_message(embed=embed)

async def setup(client):
    await client.add_cog(Slash(client))
