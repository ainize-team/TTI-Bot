import asyncio
import json
import logging
import logging.handlers
from typing import Callable, Dict, List, Tuple

import discord
import requests
from discord.ui import Button, View
from pydantic import HttpUrl

from enums import ResponseStatusEnum
from schemas import ImageGenerationRequest
from settings import model_settings


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def preprocess_data(
    prompt: str, steps: int, seed: int, width: int, height: int, images: int, guidance_scale: float
) -> Tuple[ImageGenerationRequest, List[str]]:
    warning_message_list = []
    if width % model_settings.model_image_unit_size != 0:
        warning_message_list.append(f"width is a multiple of {model_settings.model_image_unit_size}")
        warning_message_list.append(
            f"change width value from {width} to {(width // model_settings.model_image_unit_size) * model_settings.model_image_unit_size}"
        )
        width = (width // model_settings.model_image_unit_size) * model_settings.model_image_unit_size
    if height % model_settings.model_image_unit_size != 0:
        warning_message_list.append(f"height is a multiple of {model_settings.model_image_unit_size}")
        warning_message_list.append(
            f"change height value from {height} to {(height // model_settings.model_image_unit_size) * model_settings.model_image_unit_size}"
        )
        height = (height // model_settings.model_image_unit_size) * model_settings.model_image_unit_size
    image_generation_request = ImageGenerationRequest(
        prompt=prompt,
        steps=steps,
        seed=seed,
        width=width,
        height=height,
        images=images,
        guidance_scale=guidance_scale,
    )
    return image_generation_request, warning_message_list


def build_error_message(title: str, description: str) -> discord.Embed:
    return build_message(title=title, description=description, colour=discord.Colour.red())


def build_message(title: str, description: str, colour: discord.Colour) -> discord.Embed:
    if len(title) > 256:
        title = title[:253] + "..."
    return discord.Embed(title=title, colour=colour, description=description)


def post_req(
    url: str, data: Dict, headers: Dict = {"Content-Type": "application/json", "accept": "application/json"}
) -> Tuple[bool, Dict]:
    res = requests.post(
        url,
        headers=headers,
        data=json.dumps(data),
    )
    if res.status_code == 200:
        return True, res.json()
    else:
        return False, res.text


def get_req(url: str) -> Tuple[bool, Dict]:
    res = requests.get(
        url,
        headers={
            "accept": "application/json",
        },
    )
    if res.status_code == 200:
        return True, res.json()
    else:
        return False, res.text


async def get_results(
    url: str,
    n: int,
    user: str,
    interaction: discord.Interaction,
    message: discord.Embed,
) -> Tuple[bool, Dict]:
    prev_status: ResponseStatusEnum = ResponseStatusEnum.PENDING
    mentions = discord.AllowedMentions(users=True)
    for step in range(n):
        logger.info(f"Step : {step}/300")
        is_success, res = get_req(url)
        if not is_success:
            continue
        status = res["status"]
        if status == ResponseStatusEnum.COMPLETED:
            return True, res
        elif status != prev_status:
            await interaction.edit_original_response(
                embed=message,
                content=f"{user} Your task's status is updated from {prev_status} to {status}",
                allowed_mentions=mentions,
            )
            prev_status = status
        await asyncio.sleep(1)
    else:
        return False, {}


def individual_image_button(image_url: HttpUrl, title: str, description: str, user) -> Callable:
    mentions = discord.AllowedMentions(users=True)

    async def call_back(interaction: discord.Interaction):
        async def upsacle(interaction: discord.Interaction):
            is_success, res = post_req(
                url=f"{model_settings.model_upscale_endpoint}/upscale/url?url={image_url}",
                headers={"accept": "application/json"},
                data={},
            )
            if is_success:
                task_id = res["task_id"]
                message_embed = build_message(
                    title=f"Upscale > {title}", colour=discord.Colour.blue(), description=f"task id : {task_id}"
                )
                await interaction.response.send_message(
                    embed=message_embed,
                    content=f"{user} Your task is successfully requested.",
                    allowed_mentions=mentions,
                    ephemeral=True,
                )
                is_success, res = await get_results(
                    url=f"{model_settings.model_upscale_endpoint}/result/{task_id}",
                    n=300,
                    user=user,
                    interaction=interaction,
                    message=message_embed,
                )
                if is_success:
                    output = res["output"]
                    message_embed.set_image(url=output)
                    content_message = f"{user} Your task is completed."
                    message_embed.colour = discord.Colour.green()
                    await interaction.edit_original_response(
                        content=content_message,
                        embed=message_embed,
                        allowed_mentions=mentions,
                    )
                    return
                else:
                    error_embed = build_error_message(
                        title="TimeOut Error",
                        description=f"Your task cannot be generated because there are too many tasks on the server.\nIf you want to get your results late, let the community manager know your task id{task_id}.",
                    )
                    await interaction.edit_original_response(embed=error_embed)
                    return
            else:
                error_embed = build_error_message(
                    title="Upscale Request Error",
                    description="The request failed.\nPlease try again in a momentarily.\nIf the situation repeats, please let our community manager know.",
                )
                await interaction.response.send_message(embed=error_embed, ephemeral=True)

        embed = build_message(title=title, description=description, colour=discord.Colour.green())
        embed.set_image(url=image_url)
        view = View(timeout=None)
        upscale_button = Button(label="upscale", style=discord.ButtonStyle.gray)
        upscale_button.callback = upsacle
        view.add_item(upscale_button)

        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

    return call_back
