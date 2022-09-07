from pydantic import BaseModel, Field

from settings import model_settings


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="try adding increments to your prompt such as 'oil on canvas', 'a painting', 'a book cover'",
    )
    steps: int = Field(
        default=45, ge=1, le=100, description="How many steps to spend generating (diffusing) your image."
    )
    seed: int = Field(default=1, ge=0, le=2147483647)
    width: int = Field(
        default=model_settings.model_image_minimum_size,
        ge=model_settings.model_image_minimum_size,
        le=model_settings.model_image_maximum_size,
        description="The width of the generated image.",
    )
    height: int = Field(
        default=model_settings.model_image_minimum_size,
        ge=model_settings.model_image_minimum_size,
        le=model_settings.model_image_maximum_size,
        description="The height of the generated image.",
    )
    images: int = Field(2, ge=1, le=4, description="How many images you wish to generate")
    guidance_scale: float = Field(
        7,
        ge=0,
        le=20,
        description="How much the image will be like your prompt. Higher values keep your image closer to your prompt.",
    )
