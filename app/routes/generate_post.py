from fastapi import APIRouter, HTTPException, Form
import io
from PIL import Image
from app.services.image_processing import extract_color_proportions
from app.models.item import Item
from app.services.prompt_building import build_prompt_generation, build_prompt_tagline
from app.services.api_calls import fetch_response, fetch_image_response
from app.services.image_processing import overlay_logo, add_text_overlay, generate_random_hex_color
from app.services.s3 import upload_image_to_s3, BUCKET_NAME
from typing_extensions import Annotated
from app.utils.download_image_from_url import download_image_from_url
from app.core.logger import logger
import uuid
from app.services.prompt_building import build_dynamic_image_prompt
from app.errors.style_validation_error import StyleValidationError, StyleRequest
from app.services.content_moderation import is_content_explicit
import traceback

router = APIRouter()

@router.post("/generate-post")
async def generate_post(
    length: Annotated[int, Form(..., ge=10, le=700)] = 150,
    bzname: str = Form(...),
    purpose: str = Form(...),
    preferredTone: str = Form(...),
    website: Annotated[str, Form(...)] = "",
    hashtags: bool = Form(...),
    style: str = Form(...),
    logo: str = Form(...),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"
):
    # Explicit content check 
    if await is_content_explicit(purpose):
        logger.error("Explicit content detected in purpose: ")
        raise HTTPException(
            status_code=400,
            detail="Explicit content detected in the purpose. It is against the policy."
        )

    try:
        # Style validation
        style_request = StyleRequest(style=style)
        validated_style = style_request.style

        # Create item object
        item = Item(
            length=length,
            bzname=bzname,
            purpose=purpose,
            preferredTone=preferredTone,
            website=website,
            hashtags=hashtags,
            style=validated_style or "digital",
            model=model
        )

        # Main processing logic
        try:
            # Process logo image
            logo_bytes = await download_image_from_url(logo)
            output_image = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            color_proportions = extract_color_proportions(output_image)
            colors = ", ".join([sub['colorCode'] for sub in color_proportions])

            # Generate post content
            prompt = build_prompt_generation(item)
            logger.info(f"Generating post with prompt: {prompt}")
            post = fetch_response(prompt, item.model)

            # Generate tagline
            tagline_prompt = build_prompt_tagline(item, post.content[0].text)
            logger.info(f"Generating tagline with prompt: {tagline_prompt}")
            tagline = fetch_response(tagline_prompt, "claude-3-5-sonnet-20241022").content[0].text
            logger.info(f"Generated tagline: {tagline}")

            # Generate and process image
            image_prompt_dynamic = build_dynamic_image_prompt(post.content[0].text, item.style, colors)
            image = fetch_image_response(image_prompt_dynamic, "ultra")
            text_image = add_text_overlay(image, tagline, generate_random_hex_color())
            final_image_bytes = overlay_logo(text_image, logo_bytes)

            # Upload to S3
            image_name = f"gen_post_{uuid.uuid4().hex}.jpeg"
            upload_image_to_s3(final_image_bytes, image_name)
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"

            return {
                "post": post.content[0].text,
                "tagline": tagline,
                "image_url": s3_url,
                "input_tokens": post.usage.input_tokens,
                "output_tokens": post.usage.output_tokens,
            }

        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            logger.debug(traceback.format_exc())
            raise HTTPException(status_code=500, detail="Content generation failed")

    except StyleValidationError as e:
        logger.error(f"Style validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise any intentionally thrown HTTPExceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected system error: {str(e)}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")