from fastapi import APIRouter, Form, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
from urllib.parse import urlparse
import traceback
import io
from PIL import Image
import uuid

from app.services.image_processing import remove_background, extract_color_proportions
from app.utils.download_image_from_url import download_image_from_url
from app.core.logger import logger

router = APIRouter()

def validate_image_url(url: str) -> None:
    """Validate if the provided URL is properly formatted and supported."""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URL format")
    
    supported_schemes = {'http', 'https'}
    if parsed.scheme not in supported_schemes:
        raise ValueError(f"URL scheme must be one of: {', '.join(supported_schemes)}")
    
    supported_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    if not any(parsed.path.lower().endswith(ext) for ext in supported_extensions):
        raise ValueError(f"Image format must be one of: {', '.join(supported_extensions)}")

@router.post("/process-image/", response_model=Dict[str, Any])
async def process_image(file: str = Form(...)) -> JSONResponse:
    """
    Process an image by removing its background and extracting color proportions.
    
    Args:
        file (str): URL of the image to process
        
    Returns:
        JSONResponse: Color proportions or error message
        
    Raises:
        HTTPException: Various exceptions based on the error type
    """
    request_id = str(uuid.uuid4())
    
    logger.info(f"Starting image processing request", extra={
        "request_id": request_id,
        "image_url": file
    })
    
    try:
        # Validate input URL
        validate_image_url(file)
        
        # Download and process image
        logger.debug("Downloading image", extra={"request_id": request_id})
        image_bytes = await download_image_from_url(file)
        
        logger.debug("Removing background", extra={"request_id": request_id})
        #output_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        image_no_bg = remove_background(image_bytes)
        
        logger.debug("Extracting color proportions", extra={"request_id": request_id})
        color_proportions = extract_color_proportions(image_no_bg)
        
        logger.info("Successfully processed image", extra={
            "request_id": request_id,
            "colors_found": len(color_proportions)
        })
        
        return JSONResponse(content={"colors": color_proportions})
        
    except ValueError as e:
        error_msg = str(e)
        logger.warning("Validation error", extra={
            "request_id": request_id,
            "error": error_msg
        })
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
        
    except TimeoutError:
        error_msg = "Request timed out while downloading image"
        logger.error(error_msg, extra={
            "request_id": request_id,
            "image_url": file
        })
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=error_msg
        )
        
    except MemoryError:
        error_msg = "Image is too large to process"
        logger.error(error_msg, extra={
            "request_id": request_id,
            "image_url": file
        })
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=error_msg
        )
        
    except Exception as e:
        error_msg = "An unexpected error occurred while processing the image"
        logger.error(
            error_msg,
            extra={
                "request_id": request_id,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )