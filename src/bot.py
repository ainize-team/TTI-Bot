import asyncio
import json
import logging
import logging.handlers
import random
from typing import Optional

import discord
import requests
from discord import app_commands
from discord.ui import Button, View
from pydantic import HttpUrl, ValidationError

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
    seed: Optional[int] = None,
    width: Optional[int] = model_settings.model_image_minimum_size,
    height: Optional[int] = model_settings.model_image_minimum_size,
    images: Optional[int] = 2,
    guidance_scale: Optional[float] = 7.0,
):
    logger.info(f"{interaction.user.name} generate image")
    try:
        try:
            if seed is None:
                seed = random.randint(0, 2147483647)
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
        except ValidationError as validation_error:
            error_message_list = []
            for error in json.loads(validation_error.json()):
                loc = error["loc"][0]
                msg = error["msg"]
                error_message_list.append(f"{loc} : {msg}")
            error_message = "\n".join(error_message_list)
            error_embed = discord.Embed(
                title="Input Validation Error", colour=discord.Colour.red(), description=error_message
            )
            logger.error(f"{interaction.user.name} ValidationError")
            await interaction.response.send_message(embed=error_embed)
            return
        except Exception as unknown_error:
            error_embed = discord.Embed(
                title="Unknown Error",
                colour=discord.Colour.red(),
                description=f"Unknown error occurred.\nPlease share the error with our community manager.\nError: {unknown_error}",
            )
            await interaction.response.send_message(embed=error_embed)
            return

        logger.info(f"{interaction.user.name} generate image - request task")
        request_data = image_generation_request.dict()
        logger.info(f"Data : {request_data}")
        post_res = requests.post(
            f"{model_settings.model_endpoint}/generate",
            headers={"Content-Type": "application/json", "accept": "application/json"},
            data=json.dumps(request_data),
        )
        if post_res.status_code == 200:
            task_id = post_res.json()["task_id"]
            user_mention = interaction.user.mention
            mentions = discord.AllowedMentions(users=True)
            message_embed = discord.Embed(
                title=f"Prompt: {image_generation_request.prompt}",
                colour=discord.Colour.blue(),
                description=f"task_id: {task_id}",
            )
            await interaction.response.send_message(
                embed=message_embed,
                content=f"{user_mention} Your task is successfully requested.",
                allowed_mentions=mentions,
            )
            prev_status: ResponseStatusEnum = ResponseStatusEnum.PENDING
            for step in range(300):
                logger.info(f"Step : {step}/300")
                get_res = requests.get(
                    f"{model_settings.model_endpoint}/result/{task_id}",
                    headers={
                        "accept": "application/json",
                    },
                )
                if get_res.status_code == 200:
                    status = get_res.json()["status"]
                    if status == ResponseStatusEnum.COMPLETED:

                        def on_click_button(image_url: HttpUrl):
                            async def call_back(interaction: discord.Interaction):

                                embed = discord.Embed(
                                    title=f"Prompt: {image_generation_request.prompt}",
                                    colour=discord.Colour.green(),
                                    description=f"task id: {task_id}",
                                )
                                embed.set_image(url=image_url)
                                await interaction.response.send_message(embed=embed, ephemeral=True)

                            return call_back

                        result = get_res.json()["result"]
                        button_list = [
                            Button(label=f"Image #{i + 1}", style=discord.ButtonStyle.gray)
                            for i in range(image_generation_request.images)
                        ]
                        view = View(timeout=None)
                        for i in range(image_generation_request.images):
                            if result[str(i + 1)]["is_filtered"]:
                                button_list[i].callback = on_click_button(result[str(i + 1)]["origin_url"])
                            else:
                                button_list[i].callback = on_click_button(result[str(i + 1)]["url"])
                            view.add_item(button_list[i])
                        message_embed.set_image(url=result["grid"]["url"])
                        if sum([each["is_filtered"] for each in result.values()]):
                            warning_message_list.append("Potential NSFW content was detected in one or more images.")
                            warning_message_list.append(
                                "If you want to see the original image, press the button below."
                            )
                        if len(warning_message_list) != 0:
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
                    elif status != prev_status:
                        await interaction.edit_original_response(
                            embed=message_embed,
                            content=f"{user_mention} Your task's status is updated from {prev_status} to {status}",
                            allowed_mentions=mentions,
                        )
                        prev_status = status
                    await asyncio.sleep(1)
            else:
                error_embed = discord.Embed(
                    title="TimeOut Error",
                    colour=discord.Colour.red(),
                    description=f"Your task cannot be generated because there are too many tasks on the server.\nIf you want to get your results late, let the community manager know your task id{task_id}.",
                )
                await interaction.edit_original_response(embed=error_embed)
        else:
            logger.error("Error :", post_res.text)
            error_embed = discord.Embed(
                title="Request Error",
                colour=discord.Colour.red(),
                description="The request failed.\nPlease try again in a momentarily.\nIf the situation repeats, please let our community manager know.",
            )
            await interaction.response.send_message(embed=error_embed)
    except Exception as unknown_error:
        error_embed = discord.Embed(
            title="Unknown Error",
            colour=discord.Colour.red(),
            description=f"Unknown error occurred.\nPlease share the error with our community manager.\nError: {unknown_error}",
        )
        await interaction.response.send_message(embed=error_embed)


# TODO: Find Better way
@client.tree.command(guild=GUILD, name="help", description="Show help for bot")
async def help(interaction: discord.Interaction):
    generate_parameters = [
        {
            "name": "prompt",
            "value": "A description of what you'd like the machine to generate.",
            "condition": "required | string",
        },
        {
            "name": "steps",
            "value": "How many steps to spend generating (diffusing) your image.",
            "condition": "integer | min: 1 | max: 100 | default: 45",
        },
        {
            "name": "seed",
            "value": "The seed used to generate your image.",
            "condition": "integer | min: 0 | max: 2147483647 | default: random integer",
        },
        {
            "name": "width",
            "value": "The width of the generated image.",
            "condition": f"integer | min: {model_settings.model_image_minimum_size} | max: {model_settings.model_image_maximum_size} | default: {model_settings.model_image_minimum_size}",
        },
        {
            "name": "height",
            "value": "The height of the generated image.",
            "condition": f"integer | min: {model_settings.model_image_minimum_size} | max: {model_settings.model_image_maximum_size} | default: {model_settings.model_image_minimum_size}",
        },
        {
            "name": "images",
            "value": "How many images you wish to generate.",
            "condition": "integer | min: 1 | max: 4 | default: 2",
        },
        {
            "name": "guidance_scale",
            "value": "How much the image will be like your prompt. Higher values keep your image closer to your prompt.",
            "condition": "number | min: 0 | max: 20 | default: 7",
        },
    ]
    generate_title = "/generate"
    generate_description = "\n>".join(
        [f" - `{each['name']}` \n> {each['value']}\n> {each['condition']}" for each in generate_parameters]
    )

    content = f"**{generate_title}** \n>{generate_description}"
    await interaction.response.send_message(content=content)


client.run(discord_settings.discord_bot_token)
