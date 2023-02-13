import asyncio
import json
import logging
import logging.handlers
import random
from typing import Callable, Dict, List, Optional, Tuple
from urllib import parse

import discord
import requests
from discord.ui import Button, View

from enums import EnvEnum, ErrorMessage, ErrorTitle, ModelEnum, ResponseStatusEnum, SchedulerType, WarningMessages
from schemas import ImageGenerationDiscordParams, ImageGenerationParams
from settings import discord_bot_settings, model_settings


def get_logger(name):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
    handler.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


logger = get_logger(__name__)


def preprocess_data(
    prompt: str,
    steps: int,
    seed: int,
    width: int,
    height: int,
    images: int,
    guidance_scale: float,
    model_id: ModelEnum,
    negative_prompt: Optional[str],
    scheduler_type: SchedulerType,
) -> Tuple[ImageGenerationParams, List[str]]:
    warning_message_list = []
    if width % model_settings.image_unit_size != 0:
        warning_message_list.append(f"width is a multiple of {model_settings.image_unit_size}")
        warning_message_list.append(
            f"change width value from {width} to {(width // model_settings.image_unit_size) * model_settings.image_unit_size}"
        )
        width = (width // model_settings.image_unit_size) * model_settings.image_unit_size
    if height % model_settings.image_unit_size != 0:
        warning_message_list.append(f"height is a multiple of {model_settings.image_unit_size}")
        warning_message_list.append(
            f"change height value from {height} to {(height // model_settings.image_unit_size) * model_settings.image_unit_size}"
        )
        height = (height // model_settings.image_unit_size) * model_settings.image_unit_size
    image_generation_request = ImageGenerationParams(
        prompt=prompt,
        steps=steps,
        seed=seed,
        width=width,
        height=height,
        images=images,
        guidance_scale=guidance_scale,
        model_id=model_id,
        negative_prompt=negative_prompt,
        scheduler_type=scheduler_type,
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
        logger.info(f"Step : {step}/{n}")
        is_success, res = get_req(url)
        if not is_success:
            logger.error(f"Failed To Get Req : {res}")
            await asyncio.sleep(1)
            continue
        status = res["status"]
        if status == ResponseStatusEnum.COMPLETED:
            return True, res
        if status == ResponseStatusEnum.ERROR:
            return False, res
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


async def get_tx_hash(
    url: str,
    n: int,
) -> Tuple[bool, Dict]:
    for step in range(n):
        logger.info(f"Step : {step}/{n}")
        is_success, res = get_req(url)
        if not is_success:
            logger.error(f"Failed To Get Req : {res}")
            await asyncio.sleep(1)
            continue
        status = res["status"]
        if status == ResponseStatusEnum.COMPLETED:
            if ResponseStatusEnum.COMPLETED in res["tx_hash"]:
                return True, res
        if status == ResponseStatusEnum.ERROR:
            return False, res
        await asyncio.sleep(1)
    else:
        return False, {}


def up_scale_image_button(image_url: str, title: str) -> Callable:
    mentions = discord.AllowedMentions(users=True)

    async def call_back(interaction: discord.Interaction):
        user = interaction.user.mention
        message_embed = build_message(title=f"Upscale > {title}", colour=discord.Colour.blue(), description="")
        await interaction.response.send_message(
            embed=message_embed,
            allowed_mentions=mentions,
            ephemeral=True,
        )
        is_success, res = post_req(
            url=f"{model_settings.upscale_endpoint}/upscale/url?url={image_url}",
            headers={"accept": "application/json"},
            data={},
        )
        if is_success:
            task_id = res["task_id"]
            message_embed = build_message(
                title=f"Upscale > {title}", colour=discord.Colour.blue(), description=f"task id: {task_id}"
            )
            await interaction.edit_original_response(
                embed=message_embed,
                content=f"{user} Your task is successfully requested.",
                allowed_mentions=mentions,
            )
            is_success, res = await get_results(
                url=f"{model_settings.upscale_endpoint}/result/{task_id}",
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
                    description=f"Your task cannot be generated because there are too many tasks on the server.\nIf you want to get your results late, let the community manager know your task id: {task_id}.",
                )
                await interaction.edit_original_response(embed=error_embed)
                return
        else:
            error_embed = build_error_message(
                title="Upscale Request Error",
                description="The request failed.\nPlease try again in a momentarily.\nIf the situation repeats, please let our community manager know.",
            )
            await interaction.edit_original_response(embed=error_embed)
            return

    return call_back


def individual_image_button(image_url: str, title: str, description: str) -> Callable:
    async def call_back(interaction: discord.Interaction):
        embed = build_message(title=title, description=description, colour=discord.Colour.green())
        embed.set_image(url=image_url)
        view = View(timeout=None)
        upscale_button = Button(label="Upscale", style=discord.ButtonStyle.gray)
        upscale_button.callback = up_scale_image_button(image_url, title)
        view.add_item(upscale_button)

        await interaction.response.send_message(embed=embed, ephemeral=True, view=view)

    return call_back


def re_generate_button(image_generation_request: ImageGenerationParams) -> Callable:
    # TODO: remove duplicate code
    async def call_back(interaction: discord.Interaction):
        seed = random.randint(0, 4294967295)
        # Is it possible?
        while image_generation_request.seed == seed:
            seed = random.randint(0, 4294967295)
        image_generation_request.seed = seed
        model_endpoint = model_settings.endpoint

        message_embed = build_message(
            title=f"Prompt: {image_generation_request.prompt}",
            description="",
            colour=discord.Colour.blue(),
        )

        mentions = discord.AllowedMentions(users=True)
        await interaction.response.send_message(
            embed=message_embed,
            allowed_mentions=mentions,
        )

        message = await interaction.original_response()
        message_id = str(message.id)
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        channel_id = str(interaction.channel.id)

        discord_data = ImageGenerationDiscordParams(
            user_id=user_id,
            guild_id=guild_id,
            channel_id=channel_id,
            message_id=message_id,
        )
        request_data = {
            "discord": discord_data.dict(),
            "params": image_generation_request.dict(),
        }
        logger.info(f"Data : {request_data}")

        is_success, res = post_req(url=f"{model_endpoint}/generate", data=request_data)

        if is_success:
            task_id = res["task_id"]
            user_mention = interaction.user.mention
            model_id = image_generation_request.model_id
            message_embed = build_message(
                title=f"Prompt: {image_generation_request.prompt}",
                description=f"task_id: {task_id}\nmodel_id: {model_id}",
                colour=discord.Colour.blue(),
            )
            await interaction.edit_original_response(
                embed=message_embed,
                content=f"{user_mention} Your task is successfully requested.",
                allowed_mentions=mentions,
            )
            is_success, res = await get_results(
                url=f"{model_endpoint}/tasks/{task_id}/images",
                n=300,
                user=user_mention,
                interaction=interaction,
                message=message_embed,
            )
            if is_success:
                button_list = [
                    Button(label=f"#{i + 1}", style=discord.ButtonStyle.gray)
                    for i in range(image_generation_request.images)
                ]
                view = View(timeout=None)
                result = res["result"]
                for i in range(image_generation_request.images):
                    if result[str(i + 1)]["is_filtered"]:
                        button_list[i].callback = individual_image_button(
                            result[str(i + 1)]["origin_url"],
                            title=f"Prompt: {image_generation_request.prompt}",
                            description=f"task_id: {task_id}\nmodel_id: {model_id}",
                        )
                    else:
                        button_list[i].callback = individual_image_button(
                            result[str(i + 1)]["url"],
                            title=f"Prompt: {image_generation_request.prompt}",
                            description=f"task_id: {task_id}\nmodel_id: {model_id}",
                        )
                    view.add_item(button_list[i])
                re_gen_button = Button(label="🔄", style=discord.ButtonStyle.gray)
                re_gen_button.callback = re_generate_button(image_generation_request)
                view.add_item(re_gen_button)
                message_embed.set_image(url=result["grid"]["url"])
                warning_message_list = []
                if sum([each["is_filtered"] for each in result.values()]):
                    warning_message_list.append(WarningMessages.NSFW)
                if len(warning_message_list) != 0:
                    warning_message_list.insert(0, f"model_id: {model_id}")
                    warning_message_list.insert(0, f"task_id: {task_id}")
                    message_embed.colour = discord.Colour.orange()
                    message_embed.description = "\n".join(warning_message_list)
                    await interaction.edit_original_response(
                        content=f"{user_mention} Your task is completed.",
                        embed=message_embed,
                        allowed_mentions=mentions,
                        view=view,
                    )
                else:
                    content_message = f"{user_mention} Your task is completed."
                    message_embed.colour = discord.Colour.green()
                    await interaction.edit_original_response(
                        content=content_message,
                        embed=message_embed,
                        allowed_mentions=mentions,
                        view=view,
                    )
                return
            else:
                if res:
                    error_embed = build_error_message(
                        title=ErrorTitle.UNKNOWN,
                        description=ErrorMessage.UNKNOWN,
                    )
                else:
                    error_embed = build_error_message(
                        title=ErrorTitle.TIMEOUT,
                        description=f"Your task cannot be generated because there are too many tasks on the server.\nIf you want to get your results late, let the community manager know your task id {task_id}.",
                    )
                    await interaction.edit_original_response(embed=error_embed)
                return

    return call_back


def get_twitter_url(task_id: str) -> str:
    def encode_uri_component(text: str) -> str:
        return parse.quote(text)

    twitter_base_url = "https://twitter.com/intent/tweet"
    image_url = f"https://aindao-text-to-art.ainetwork.xyz/{task_id}"
    if discord_bot_settings.bot_env == EnvEnum.DEV:
        image_url = f"https://aindao-text-to-art-dev.ainetwork.xyz/{task_id}"
    main_text = "It AIN't difficult to draw a picture if you use Text-to-art scheme through #AIN_DAO discord - click the image below to create your own image & earn #AIN\n@ainetwork_ai #AINetwork #stablediffusion #text2art"
    twitter_get_twitter_url = f"{twitter_base_url}?text={encode_uri_component(main_text)}&url={image_url}"
    return twitter_get_twitter_url


def get_tx_insight_url(tx_hash: str) -> str:
    if discord_bot_settings.bot_env == EnvEnum.DEV:
        prefix = "testnet-"
    else:
        prefix = ""
    tx_insight_url = f"https://{prefix}insight.ainetwork.ai/transactions/{tx_hash}"
    return tx_insight_url
