from pydantic import BaseModel, Field

from settings import model_settings


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="A description of what you'd like the machine to generate.",
    )
    user_id: str = Field("0", description="The user's unique ID.")
    guild_id: str = Field("0", description="The guild's ID.")
    channel_id: str = Field("0", description="The channel ID.")
    message_id: str = Field("0", description="The message ID.")
    steps: int = Field(
        default=45, ge=1, le=100, description="How many steps to spend generating (diffusing) your image."
    )
    seed: int = Field(default=1, ge=0, le=2147483647)
    width: int = Field(
        default=model_settings.image_minimum_size,
        ge=model_settings.image_minimum_size,
        le=model_settings.image_maximum_size,
        description="The width of the generated image.",
    )
    height: int = Field(
        default=model_settings.image_minimum_size,
        ge=model_settings.image_minimum_size,
        le=model_settings.image_maximum_size,
        description="The height of the generated image.",
    )
    images: int = Field(2, ge=1, le=4, description="How many images you wish to generate")
    guidance_scale: float = Field(
        7,
        ge=0,
        le=20,
        description="How much the image will be like your prompt. Higher values keep your image closer to your prompt.",
    )
