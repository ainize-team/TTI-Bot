from pydantic import BaseSettings, Field, HttpUrl


class DiscordSettings(BaseSettings):
    bot_token: str = Field(..., description="Discord Bot Token")
    guild_id: str = Field(..., description="Discord Guild ID")


class ModelSettings(BaseSettings):
    # TODO: get url from database
    endpoint_v14: HttpUrl = Field(..., description="Stable Diffusion v1.4 Endpoint")
    endpoint_v15: HttpUrl = Field(..., description="Stable Diffusion v1.5 Endpoint")
    endpoint_v20: HttpUrl = Field(..., description="Stable Diffusion v2.0 Endpoint")
    upscale_endpoint: HttpUrl = Field(..., description="Super Resolution Model Endpoint")
    # TODO: get image min/max size from database
    image_minimum_size: int = 512
    image_maximum_size: int = 1024
    image_unit_size: int = 64


discord_settings = DiscordSettings()
model_settings = ModelSettings()
