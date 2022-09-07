from pydantic import BaseSettings, Field, HttpUrl


class DiscordSettings(BaseSettings):
    discord_bot_token: str = Field(..., description="Discord Bot Token")
    discord_guild_id: str = Field(..., description="Discord Guild ID")


class ModelSettings(BaseSettings):
    model_endpoint: HttpUrl = Field(..., description="Diffusion Model Endpoint")
    model_image_minimum_size: int = 512
    model_image_maximum_size: int = 1024
    model_image_unit_size: int = 64


discord_settings = DiscordSettings()
model_settings = ModelSettings()
