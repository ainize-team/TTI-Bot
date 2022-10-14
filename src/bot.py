import json
import random
from typing import Optional

import discord
from discord import app_commands
from discord.ui import Button, View
from pydantic import ValidationError

from client import TextToImageClient
from settings import discord_settings, model_settings
from utils import (
    build_error_message,
    build_message,
    get_logger,
    get_results,
    individual_image_button,
    post_req,
    preprocess_data,
)


GUILD = discord.Object(id=discord_settings.guild_id)

logger = get_logger(__name__)

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
    width: Optional[int] = model_settings.image_minimum_size,
    height: Optional[int] = model_settings.image_minimum_size,
    images: Optional[int] = 2,
    guidance_scale: Optional[float] = 7.0,
):
    logger.info(f"{interaction.user.name} generate image")
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)
    channel_id = str(interaction.channel.id)
    message_id = "0"  # interaction.message.id
    logger.info(f"{user_id} {guild_id} {channel_id} {message_id}")
    try:
        if seed is None:
            seed = random.randint(0, 4294967295)
        try:
            image_generation_request, warning_message_list = preprocess_data(
                prompt=prompt,
                user_id=user_id,
                guild_id=guild_id,
                channel_id=channel_id,
                message_id=message_id,
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
            error_embed = build_error_message(title="Input Validation Error", description=error_message)
            logger.error(f"{interaction.user.name} ValidationError")
            await interaction.response.send_message(embed=error_embed)
            return
        except Exception as unknown_error:
            error_message = (
                f"Unknown error occurred.\nPlease share the error with our community manager.\nError: {unknown_error}"
            )
            error_embed = build_error_message(title="Unknown Error", description=error_message)
            await interaction.response.send_message(embed=error_embed)
            return
        logger.info(f"{interaction.user.name} generate image - request task")

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
    except Exception as unknown_error:
        error_message = (
            f"Unknown error occurred.\nPlease share the error with our community manager.\nError: {unknown_error}"
        )
        error_embed = build_error_message(title="Unknown Error", description=error_message)
        await interaction.response.send_message(embed=error_embed)
        return
    try:
        message = await interaction.original_response()
        message_id = str(message.id)
        image_generation_request.message_id = message_id
        request_data = image_generation_request.dict()
        logger.info(f"Data : {request_data}")
        is_success, res = post_req(url=f"{model_settings.endpoint}/generate", data=request_data)
        if is_success:
            task_id = res["task_id"]
            user_mention = interaction.user.mention
            message_embed = build_message(
                title=f"Prompt: {image_generation_request.prompt}",
                description=f"task_id: {task_id}",
                colour=discord.Colour.blue(),
            )
            logger.info("Here2")
            await interaction.edit_original_response(
                embed=message_embed,
                content=f"{user_mention} Your task is successfully requested.",
                allowed_mentions=mentions,
            )
            is_success, res = await get_results(
                url=f"{model_settings.endpoint}/result/{task_id}",
                n=300,
                user=user_mention,
                interaction=interaction,
                message=message_embed,
            )
            if is_success:
                button_list = [
                    Button(label=f"Image #{i + 1}", style=discord.ButtonStyle.gray)
                    for i in range(image_generation_request.images)
                ]
                view = View(timeout=None)
                result = res["result"]
                for i in range(image_generation_request.images):
                    if result[str(i + 1)]["is_filtered"]:
                        button_list[i].callback = individual_image_button(
                            result[str(i + 1)]["origin_url"],
                            title=f"Prompt: {image_generation_request.prompt}",
                            description=f"task id: {task_id}",
                            user=user_mention,
                        )
                    else:
                        button_list[i].callback = individual_image_button(
                            result[str(i + 1)]["url"],
                            title=f"Prompt: {image_generation_request.prompt}",
                            description=f"task id: {task_id}",
                            user=user_mention,
                        )
                    view.add_item(button_list[i])

                message_embed.set_image(url=result["grid"]["url"])
                if sum([each["is_filtered"] for each in result.values()]):
                    warning_message_list.append("Potential NSFW content was detected in one or more images.")
                    warning_message_list.append("If you want to see the original image, press the button below.")
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
            else:
                error_embed = build_error_message(
                    title="TimeOut Error",
                    description=f"Your task cannot be generated because there are too many tasks on the server.\nIf you want to get your results late, let the community manager know your task id{task_id}.",
                )
                await interaction.edit_original_response(embed=error_embed)
                return
        else:
            error_message = "The request failed.\nPlease try again in a momentarily.\nIf the situation repeats, please let our community manager know."
            error_embed = build_error_message(title="Request Error", description=error_message)
            await interaction.response.edit_original_response(embed=error_embed)
    except Exception as unknown_error:
        error_message = (
            f"Unknown error occurred.\nPlease share the error with our community manager.\nError: {unknown_error}"
        )
        error_embed = build_error_message(title="Unknown Error", description=error_message)
        await interaction.edit_original_response(embed=error_embed)


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
            "condition": f"integer | min: {model_settings.image_minimum_size} | max: {model_settings.image_maximum_size} | default: {model_settings.image_minimum_size}",
        },
        {
            "name": "height",
            "value": "The height of the generated image.",
            "condition": f"integer | min: {model_settings.image_minimum_size} | max: {model_settings.image_maximum_size} | default: {model_settings.image_minimum_size}",
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


client.run(discord_settings.bot_token)
