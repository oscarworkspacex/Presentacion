import asyncio
import base64
import os
import aiohttp
from google import genai
from google.genai.types import GenerateContentConfig
from openai import AsyncOpenAI
from models.image_prompt import ImagePrompt
from models.sql.image_asset import ImageAsset
from utils.download_helpers import download_file
from utils.get_env import get_pexels_api_key_env
from utils.get_env import get_pixabay_api_key_env
from utils.get_env import get_openai_image_model_env
from utils.get_env import get_google_image_model_env
from utils.get_env import get_image_generation_max_concurrent_env
from utils.image_provider import (
    is_pixels_selected,
    is_pixabay_selected,
    is_gemini_flash_selected,
    is_dalle3_selected,
)
from utils.asset_directory_utils import PLACEHOLDER_IMAGE_URL
from core.logging import get_logger
import uuid

logger = get_logger(__name__)

IMAGE_PROMPT_MAX_LENGTH = 400
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [2, 4, 8]

_image_generation_semaphore: asyncio.Semaphore | None = None


def _get_image_semaphore() -> asyncio.Semaphore:
    global _image_generation_semaphore
    if _image_generation_semaphore is None:
        _image_generation_semaphore = asyncio.Semaphore(
            get_image_generation_max_concurrent_env()
        )
    return _image_generation_semaphore


def sanitize_image_prompt(prompt: str) -> str:
    if len(prompt) <= IMAGE_PROMPT_MAX_LENGTH:
        return prompt
    logger.warning(
        "Image prompt truncated from %d to %d characters",
        len(prompt),
        IMAGE_PROMPT_MAX_LENGTH,
    )
    return prompt[:IMAGE_PROMPT_MAX_LENGTH].rstrip()


def is_retryable_image_error(error: Exception) -> bool:
    message = str(error).lower()
    retryable_patterns = (
        "rate limit",
        "429",
        "500",
        "502",
        "503",
        "504",
        "timeout",
        "timed out",
        "overloaded",
        "temporarily unavailable",
        "connection reset",
        "connection error",
    )
    return any(pattern in message for pattern in retryable_patterns)


async def generate_with_retry(coro_factory):
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return await coro_factory()
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1 and is_retryable_image_error(e):
                delay = RETRY_BACKOFF_SECONDS[attempt]
                logger.warning(
                    "Retryable image error (attempt %d/%d), retrying in %ds: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    delay,
                    e,
                )
                await asyncio.sleep(delay)
                continue
            raise
    if last_error:
        raise last_error
    raise Exception("Image generation failed after retries")


class ImageGenerationService:

    def __init__(self, output_directory: str):
        self.output_directory = output_directory
        self.image_gen_func = self.get_image_gen_func()

    def get_image_gen_func(self):
        if is_pixabay_selected():
            return self.get_image_from_pixabay
        elif is_pixels_selected():
            return self.get_image_from_pexels
        elif is_gemini_flash_selected():
            return self.generate_image_google
        elif is_dalle3_selected():
            return self.generate_image_openai
        return None

    def is_stock_provider_selected(self):
        return is_pixels_selected() or is_pixabay_selected()

    async def generate_image(self, prompt: ImagePrompt) -> str | ImageAsset:
        """
        Generates an image based on the provided prompt.
        - If no image generation function is available, returns a placeholder image.
        - If the stock provider is selected, it uses the prompt directly,
        otherwise it uses the full image prompt with theme.
        - Output Directory is used for saving the generated image not the stock provider.
        """
        if not self.image_gen_func:
            logger.warning(
                "No image generation function found. IMAGE_PROVIDER may be unset or invalid."
            )
            return PLACEHOLDER_IMAGE_URL

        raw_prompt = prompt.get_image_prompt(
            with_theme=not self.is_stock_provider_selected()
        )
        image_prompt = sanitize_image_prompt(raw_prompt)
        logger.info("Generating image for prompt: %s", image_prompt)

        try:
            if self.is_stock_provider_selected():
                image_path = await generate_with_retry(
                    lambda: self.image_gen_func(image_prompt)
                )
            else:
                async def _generate():
                    async with _get_image_semaphore():
                        return await self.image_gen_func(
                            image_prompt, self.output_directory
                        )

                image_path = await generate_with_retry(_generate)

            if not image_path:
                raise Exception("Image provider returned an empty path")

            if image_path.startswith("http"):
                return image_path

            if os.path.exists(image_path):
                return ImageAsset(
                    path=image_path,
                    is_uploaded=False,
                    extras={
                        "prompt": prompt.prompt,
                        "theme_prompt": prompt.theme_prompt,
                    },
                )

            raise Exception(f"Image not found at {image_path}")

        except Exception as e:
            logger.error("Error generating image for '%s': %s", image_prompt, e)
            return PLACEHOLDER_IMAGE_URL

    async def generate_image_openai(self, prompt: str, output_directory: str) -> str:
        model = get_openai_image_model_env()
        client = AsyncOpenAI()
        logger.info("OpenAI image generation using model: %s", model)

        try:
            result = await client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
        except Exception as e:
            raise Exception(f"OpenAI image API error: {e}") from e

        if not result.data:
            raise Exception("OpenAI returned no image data")

        image_data = result.data[0]

        if image_data.b64_json:
            image_path = os.path.join(output_directory, f"{uuid.uuid4()}.png")
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image_data.b64_json))
            if not os.path.exists(image_path):
                raise Exception(f"Saved image not found at {image_path}")
            return image_path

        if image_data.url:
            downloaded_path = await download_file(image_data.url, output_directory)
            if not downloaded_path:
                raise Exception("Failed to download image from OpenAI")
            if not os.path.exists(downloaded_path):
                raise Exception(f"Downloaded image not found at {downloaded_path}")
            return downloaded_path

        raise Exception("OpenAI response contained neither b64_json nor url")

    async def generate_image_google(self, prompt: str, output_directory: str) -> str:
        model = get_google_image_model_env()
        client = genai.Client()
        logger.info("Google image generation using model: %s", model)

        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=[prompt],
                config=GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
            )
        except Exception as e:
            raise Exception(f"Google image API error: {e}") from e

        image_path = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_path = os.path.join(output_directory, f"{uuid.uuid4()}.jpg")
                with open(image_path, "wb") as f:
                    f.write(part.inline_data.data)
                break

        if not image_path:
            raise ValueError("Gemini did not return any image data in the response")

        return image_path

    async def get_image_from_pexels(self, prompt: str) -> str:
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await session.get(
                f"https://api.pexels.com/v1/search?query={prompt}&per_page=1",
                headers={"Authorization": f"{get_pexels_api_key_env()}"},
            )
            data = await response.json()
            if not data.get("photos"):
                raise Exception(f"No Pexels results for prompt: {prompt}")
            image_url = data["photos"][0]["src"]["large"]
            return image_url

    async def get_image_from_pixabay(self, prompt: str) -> str:
        async with aiohttp.ClientSession(trust_env=True) as session:
            response = await session.get(
                f"https://pixabay.com/api/?key={get_pixabay_api_key_env()}&q={prompt}&image_type=photo&per_page=3"
            )
            data = await response.json()
            if not data.get("hits"):
                raise Exception(f"No Pixabay results for prompt: {prompt}")
            image_url = data["hits"][0]["largeImageURL"]
            return image_url
