import requests
from app.core.logger import logger
from fastapi import HTTPException

async def download_image_from_url(logo_url: str) -> bytes:
    try:
        response = requests.get(logo_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Error downloading image from URL: {e}")
        raise HTTPException(status_code=400, detail="Unable to download image from provided URL")
