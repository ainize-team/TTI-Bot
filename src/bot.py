import asyncio
import json
import logging
import logging.handlers
from typing import Optional

import discord
import requests
from discord import app_commands

from client import TextToImageClient
from enums import ResponseStatusEnum
from schemas import ImageGenerationRequest
from settings import discord_settings, model_settings


GUILD = discord.Object(id=discord_settings.discord_guild_id)


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

intents = discord.Intents.default()
client = TextToImageClient(intents=intents, guild=GUILD)


@client.tree.command(guild=GUILD, name="generate", description="Generate Image")
@app_commands.describe(
    prompt="try adding increments to your prompt such as 'oil on canvas', 'a painting', 'a book cover'",
    steps="more steps can increase quality but will take longer to generate",
    seed="Random seed",
    width="Image width",
    height="Image Height",
    images="How many images you wish to generate",
    guidance_scale="how much the prompt will influence the results",
)
async def generate(
    interaction: discord.Interaction,
    prompt: str,
    steps: Optional[int] = 45,
    seed: Optional[int] = 42,
    width: Optional[int] = 512,
    height: Optional[int] = 512,
    images: Optional[int] = 2,
    guidance_scale: Optional[float] = 7.5,
):
    logger.info(f"{interaction.user.name} generate image")
    try:
        logger.info(f"{interaction.user.name} generate image - validate user input")
        image_generation_request = ImageGenerationRequest(
            prompt=prompt,
            steps=steps,
            seed=seed,
            width=width,
            height=height,
            images=images,
            guidance_scale=guidance_scale,
        )
        logger.info(f"{interaction.user.name} generate image - request task")
        request_data = image_generation_request.dict()
        post_res = requests.post(
            f"{model_settings.model_endpoint}/generate",
            headers={"Content-Type": "application/json", "accept": "application/json"},
            data=json.dumps(request_data),
        )
        if post_res.status_code == 200:
            task_id = post_res.json()["task_id"]
            user_mention = interaction.user.mention
            mentions = discord.AllowedMentions(users=True)
            await interaction.response.send_message(f"The task was successfully requested. Task id is {task_id}")
            prev_status: ResponseStatusEnum = ResponseStatusEnum.PENDING
            for step in range(60):
                get_res = requests.get(
                    f"{model_settings.model_endpoint}/result/{task_id}",
                    headers={
                        "accept": "application/json",
                    },
                )
                if get_res.status_code == 200:
                    status = get_res.json()["status"]
                    logger.info(f"Step : {step}/30 {status}")
                    if status == ResponseStatusEnum.COMPLETED:
                        embed = discord.Embed()
                        embed.set_image(url=get_res.json()["result"]["grid"]["url"])
                        await interaction.edit_original_response(
                            content=f"{user_mention} Your task is completed.",
                            embed=embed,
                            allowed_mentions=mentions,
                        )
                        return
                    elif status != prev_status:
                        await interaction.edit_original_response(
                            content=f"{user_mention} Status Update Detected({task_id}) from {prev_status} to {status}",
                            allowed_mentions=mentions,
                        )
                        prev_status = status
                    await asyncio.sleep(1)
            else:
                logger.error(f"{interaction.user.name} Request Error: {post_res.status_code}")
                await interaction.response.send_message(f"Time Out Error : {task_id}")
        else:
            logger.error(f"Failed to request {post_res.text}")
            await interaction.response.send_message("Request Failed")
    except Exception as e:
        logger.error(f"{interaction.user.name} Error :{e}")
        await interaction.response.send_message(f"Error: {e}")


client.run(discord_settings.discord_bot_token)
