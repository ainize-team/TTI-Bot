from pydantic import BaseModel, Field

from enums import ModelEnum
from settings import model_settings
from typing import Optional


class ImageGenerationDiscordParams(BaseModel):
    user_id: str = Field(..., description="The user's unique ID.")
    guild_id: str = Field(..., description="The guild's ID.")
    channel_id: str = Field(..., description="The channel ID.")
    message_id: str = Field(..., description="The message ID.")


class ImageGenerationParams(BaseModel):
    prompt: str = Field(
        ...,
        description="A description of what you'd like the machine to generate.",
    )
    steps: int = Field(
        default=50, ge=1, le=100, description="How many steps to spend generating (diffusing) your image."
    )
    seed: int = Field(default=1, ge=0, le=4294967295)
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
    model_id: ModelEnum = Field(
        ModelEnum.STABLE_DIFFUSION_V2,
        description="name of diffusion model. stable-diffusion-v1-4, stable-diffusion-v1-5 or stable-diffusion-v2 are supported.",
    )

    negative_prompt: Optional[str] = Field(
        None,
        description="negative prompting indicates which terms you do not want to see in the resulting image.",
    )


class ImageGenerationRequest(BaseModel):
    discord: ImageGenerationDiscordParams
    params: ImageGenerationParams
