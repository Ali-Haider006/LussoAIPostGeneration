from fastapi import APIRouter, HTTPException, Form, UploadFile
from app.services.prompt_building import build_prompt_tagline, build_dynamic_image_prompt
from app.services.api_calls import fetch_response, fetch_image_response
from app.services.image_processing import overlay_logo
from typing_extensions import Annotated, Optional
from app.core.logger import logger
from app.models.item import Item
import base64

router = APIRouter()

@router.post("/regenerate-image")
async def regenerate_post(
    post: str = Form(...),
    length: Annotated[int, Form(..., ge=10, le=700)] = 150,
    bzname: str = Form(...),
    purpose: str = Form(...),
    preferredTone: str = Form(...),
    website: str = Form(...),
    hashtags: bool = Form(...),
    color_theme: Optional[str] = Form(None),
    logo: UploadFile = Form(...),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022",
):
    item = Item(
        length=length,
        bzname=bzname,
        purpose=purpose,
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
        image_prompt_dynamic = build_dynamic_image_prompt(post, tagline, item.color_theme)
        image_prompt = fetch_response(image_prompt_dynamic, "claude-3-5-sonnet-20241022").content[0].text
        logger.info(f"Generated image prompt: {image_prompt}")

        image = fetch_image_response(image_prompt, image_model)
        logo_bytes = await logo.read()
        final_image_bytes = overlay_logo(image, logo_bytes)

        image_base64 = base64.b64encode(final_image_bytes).decode('utf-8')

        # Save the image to a file for testing
        image_name = f"./overlayed_images/gen_post_{tagline}.jpeg"
        with open(image_name, 'wb') as file:
            file.write(final_image_bytes)
        return {
            "tagline": tagline,
            "image": image_base64,   
        }
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to regenerate image")
