from pydantic import BaseModel, Field, validator


class ImageGenerationRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="try adding increments to your prompt such as 'oil on canvas', 'a painting', 'a book cover'",
    )
    steps: int = Field(
        default=45, ge=1, le=100, description="more steps can increase quality but will take longer to generate"
    )
    seed: int = Field(default=1, ge=0, le=2147483647)
    width: int = Field(default=512, ge=512, le=1024)
    height: int = Field(default=512, ge=512, le=1024)
    images: int = Field(2, ge=1, le=4, description="How many images you wish to generate")
    guidance_scale: float = Field(7.5, ge=0, le=50, description="how much the prompt will influence the results")

    @validator("width")
    def validate_width(cls, v):
        # width must be a multiple of 64.
        if v % 64 != 0:
            raise ValueError("Width must be a multiple of 64")

    @validator("width")
    def validate_height(cls, v):
        # width must be a multiple of 64.
        if v % 64 != 0:
            raise ValueError("Height must be a multiple of 64")
