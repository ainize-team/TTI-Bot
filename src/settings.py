from pydantic import BaseSettings, Field, HttpUrl

from enums import EnvEnum


class DiscordBotSettings(BaseSettings):
    bot_token: str = Field(..., description="Discord Bot Token")
    guild_id: str = Field(..., description="Discord Guild ID")
    bot_env: EnvEnum = EnvEnum.DEV


class ModelSettings(BaseSettings):
    endpoint: HttpUrl = Field(..., description="Text to Art Model Endpoint")
    upscale_endpoint: HttpUrl = Field(..., description="Super Resolution Model Endpoint")
    # TODO: get image min/max size from database
    image_minimum_size: int = 512
    image_maximum_size: int = 1024
    image_unit_size: int = 64


discord_bot_settings = DiscordBotSettings()
model_settings = ModelSettings()
