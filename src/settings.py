from pydantic import BaseSettings, Field, HttpUrl


class DiscordSettings(BaseSettings):
    discord_bot_token: str = Field(..., description="Discord Bot Token")
    discord_guild_id: str = Field(..., description="Discord Guild ID")


class ModelSettings(BaseSettings):
    model_endpoint: HttpUrl = Field(..., description="Diffusion Model Endpoint")


discord_settings = DiscordSettings()
model_settings = ModelSettings()
