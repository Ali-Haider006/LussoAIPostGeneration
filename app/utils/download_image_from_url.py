import requests
from app.core.logger import logger
from fastapi import HTTPException
import httpx

async def download_image_from_url(logo_url: str) -> bytes:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(logo_url)
            response.raise_for_status()
            return response.content
    except httpx.RequestError as e:
        logger.error(f"Error downloading image from URL: {e}")
        raise HTTPException(status_code=400, detail="Unable to download image from provided URL")