from fastapi import APIRouter, HTTPException, Form
import uuid
from app.services.prompt_building import build_prompt_tagline, build_dynamic_image_prompt
from app.services.api_calls import fetch_response, fetch_image_response
from app.services.image_processing import overlay_logo, add_text_overlay, generate_random_hex_color
from typing_extensions import Annotated, Optional
from app.utils.download_image_from_url import download_image_from_url
from app.core.logger import logger
from app.models.regenerate_image import RegenerationImage
from app.services.s3 import upload_image_to_s3, BUCKET_NAME

router = APIRouter()

@router.post("/regenerate-image")
async def regenerate_image(
    post: str = Form(...),
    bzname: str = Form(...),
    preferredTone: str = Form(...),
    website: Optional[str] = "",
    hashtags: bool = Form(...),
    color_theme: Optional[str] = Form(None),
    logo: str = Form(...),
    count: int = Form(...),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022",
):
    if count >= 2:
        raise HTTPException(status_code=403, detail="Cannot regenerate more than 2 times")
    item = RegenerationImage(
        bzname=bzname,  
        preferredTone=preferredTone,
        website=website,
        hashtags=hashtags,
        color_theme=color_theme if color_theme else "vibrant color theme",
        model=model
    )
    try:
        tagline_prompt = build_prompt_tagline(item, post)
        logger.info(f"Generating tagline with prompt: {tagline_prompt}")
        tagline = fetch_response(tagline_prompt, "claude-3-5-sonnet-20241022").content[0].text
        logger.info(f"Generated tagline: {tagline}")
        image_model = "ultra"
        image_prompt_dynamic = build_dynamic_image_prompt(post, item.color_theme)
        image_prompt = fetch_response(image_prompt_dynamic, "claude-3-5-sonnet-20241022").content[0].text
        logger.info(f"Generated image prompt: {image_prompt}")

        image = fetch_image_response(image_prompt, image_model)
        if not item.color_theme or item.color_theme == "vibrant color theme" or "#" not in item.color_theme:
            image_color_theme = generate_random_hex_color()
        else:
            image_color_theme = item.color_theme.split(",")[0].strip()

        text_image = add_text_overlay(image, tagline, image_color_theme)

        logo_bytes = await download_image_from_url(logo)
        final_image_bytes = overlay_logo(text_image, logo_bytes)

        # Generate unique image name
        image_name = f"gen_post_{uuid.uuid4().hex}.jpeg"
        # Upload image to S3
        upload_image_to_s3(final_image_bytes, image_name) 
        # Generate S3 URL
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"
        return {
            "tagline": tagline,
            "image_url": s3_url,   
        }
        # Save the image to a file for testing
        # image_name = f"./overlayed_images/gen_post_{tagline}.jpeg"
        # with open(image_name, 'wb') as file:
        #     file.write(final_image_bytes)
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to regenerate image")
