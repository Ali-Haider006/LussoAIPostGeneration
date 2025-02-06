from fastapi import APIRouter, HTTPException, Form, status
from typing_extensions import Annotated, Optional
from typing import Dict, Any
import uuid
import traceback
import io
from PIL import Image
from app.services.image_processing import extract_color_proportions
from app.services.prompt_building import build_prompt_tagline_no_purpose, build_dynamic_image_prompt_purpose
from app.services.api_calls import fetch_response, fetch_image_response
from app.services.image_processing import (
    overlay_logo, 
    add_text_overlay, 
    generate_random_hex_color
)
from app.utils.download_image_from_url import download_image_from_url
from app.core.logger import logger
from app.models.regenerate_image import RegenerationImage
from app.services.s3 import upload_image_to_s3, BUCKET_NAME
from app.utils.constants import FONT_LIST
from app.services.prompt_building import build_prompt_font_selection
from app.utils.validate_font import get_valid_font

router = APIRouter()

def validate_inputs(
    post: str,
    bzname: str,
    style: Optional[str],
    logo: str,
    count: int
) -> None:
    """Validate input parameters before processing."""
    if not post.strip():
        raise ValueError("Post content cannot be empty")
    
    if not bzname.strip():
        raise ValueError("Business name cannot be empty")
    
    if style and "#" in style:
        # Validate hex color format if provided
        colors = style.split(",")
        for color in colors:
            color = color.strip()
            if not color.startswith("#") or len(color) != 7:
                raise ValueError(f"Invalid hex color format: {color}")
    
    if not logo.startswith(("http://", "https://")):
        raise ValueError("Invalid logo URL format")
    
    if count < 0:
        raise ValueError("Count cannot be negative")
    
    if count >= 2:
        raise ValueError("Cannot regenerate more than 2 times")

@router.post("/regenerate-image", response_model=Dict[str, str])
async def regenerate_image(
    purpose: str = Form(...),
    post: str = Form(...),
    bzname: str = Form(...),
    preferredTone: str = Form(...),
    website: Annotated[str, Form(...)] = "",
    hashtags: bool = Form(...),
    style: str = Form(...),
    logo: str = Form(...),
    count: int = Form(...),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022",
) -> Dict[str, str]:
    """
    Regenerate an image with text overlay and logo based on input parameters.
    
    Args:
        post (str): Post content to base the image on
        bzname (str): Business name
        preferredTone (str): Preferred tone for the content
        website (str, optional): Website URL
        hashtags (bool): Whether to include hashtags
        style (str, optional): Color theme for the image
        logo (str): URL of the logo to overlay
        count (int): Number of regeneration attempts
        model (str): AI model to use
        
    Returns:
        Dict[str, str]: Dictionary containing tagline and image URL
        
    Raises:
        HTTPException: Various exceptions based on the error type
    """
    request_id = str(uuid.uuid4())
    logger.info("Starting image regeneration request", extra={
        "request_id": request_id,
        "business_name": bzname,
        "regeneration_count": count
    })
    
    try:
        # Validate inputs
        validate_inputs(post, bzname, style, logo, count)
        
        # Initialize regeneration item
        item = RegenerationImage(
            purpose=purpose,
            bzname=bzname,
            preferredTone=preferredTone,
            website=website,
            hashtags=hashtags,
            style=style if style else "digital",
            model=model
        )
        
        # Generate tagline
        logger.debug("Generating tagline", extra={"request_id": request_id})
        tagline_prompt = build_prompt_tagline_no_purpose(item, post)
        tagline_response = fetch_response(tagline_prompt, "claude-3-5-sonnet-20241022")
        if not tagline_response or not tagline_response.content:
            raise ValueError("Failed to generate tagline")
        tagline = tagline_response.content[0].text

        logo_bytes = await download_image_from_url(logo)
        output_image = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

        color_proportions = extract_color_proportions(output_image)
        colors = ", ".join([ sub['colorCode'] for sub in color_proportions ])
        
        # Generate image prompt
        logger.debug("Generating image prompt", extra={"request_id": request_id})
        image_prompt_dynamic = build_dynamic_image_prompt_purpose(post, item.style, item.purpose, colors)
        image_prompt_response = fetch_response(image_prompt_dynamic, "claude-3-5-sonnet-20241022")
        if not image_prompt_response or not image_prompt_response.content:
            raise ValueError("Failed to generate image prompt")
        image_prompt = image_prompt_response.content[0].text
        
        # Generate and process image
        logger.debug("Generating base image", extra={"request_id": request_id})
        image = fetch_image_response(image_prompt, "ultra")
        
        # Determine color theme
        if not item.style or item.style == "digital" or "#" not in item.style:
            image_style = generate_random_hex_color()
        else:
            image_style = item.style.split(",")[0].strip()
        
        # Add overlays
        logger.debug("Adding text overlay", extra={"request_id": request_id})
        font_prompt = build_prompt_font_selection(item, tagline, FONT_LIST)

        logger.info(f"Generated font prompt: {font_prompt}")

        model_font = fetch_response(font_prompt, item.model)

        font = get_valid_font(model_font.content[0].text, FONT_LIST)

        logger.info(f"Generated font: {font}")

        final_image_bytes = add_text_overlay(image, tagline, image_style, font, logo_bytes)
        
        logger.debug("Downloading and adding logo", extra={"request_id": request_id})
        # final_image_bytes = overlay_logo(text_image, logo_bytes)
        
        # Upload to S3
        image_name = f"gen_post_{uuid.uuid4().hex}.jpeg"
        logger.debug("Uploading to S3", extra={
            "request_id": request_id,
            "image_name": image_name
        })
        await upload_image_to_s3(final_image_bytes, image_name)
        
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"
        
        logger.info("Successfully generated image", extra={
            "request_id": request_id,
            "image_url": s3_url
        })
        
        return {
            "tagline": tagline,
            "image_url": s3_url,
        }
        
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
        error_msg = "Request timed out while processing"
        logger.error(error_msg, extra={
            "request_id": request_id
        })
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=error_msg
        )
    
    except Exception as e:
        error_msg = "An unexpected error occurred while regenerating the image"
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