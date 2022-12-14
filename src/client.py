import discord
from discord import app_commands

from utils import get_logger


logger = get_logger(__name__)


class TextToImageClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, guild: discord.Object) -> None:
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.guild = guild

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def setup_hook(self):
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)
