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

# Prebuilt image URL for policy violations
PREBUILT_IMAGE_URL = "https://lussoimagestorage.s3.amazonaws.com/gen_post_0d8e8aed4e924711bfdcc9350f2f72e4.jpeg"
FALLBACK_MESSAGE = "AI generated content doesn't work for explicit policy. Goes against our policies."

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
    try:
        style_request = StyleRequest(style=style)
        validated_style = style_request.style

        item = Item(
            length=length,
            bzname=bzname,
            purpose=purpose,
            preferredTone=preferredTone,
            website=website,
            hashtags=hashtags,
            style=validated_style if validated_style else "digital",
            model=model
        )

        # Download and process the logo
        try:
            logo_bytes = await download_image_from_url(logo)
            output_image = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            color_proportions = extract_color_proportions(output_image)
            colors = ", ".join([sub['colorCode'] for sub in color_proportions])
        except Exception as e:
            logger.error(f"Error downloading or processing logo: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid logo URL or image processing failed.")

        # Generate the post content
        try:
            prompt = build_prompt_generation(item)
            logger.info(f"Generating post with prompt: {prompt}")
            post = fetch_response(prompt, item.model)
            post_content = post.content[0].text.strip()

            # Check if post content violates policies
            if post_content == FALLBACK_MESSAGE or await is_content_explicit(post_content):
                logger.warning("Explicit or fallback content detected in post")
                return {
                    "post": post_content,
                    "tagline": FALLBACK_MESSAGE,
                    "image_url": PREBUILT_IMAGE_URL,
                    "input_tokens": post.usage.input_tokens,
                    "output_tokens": post.usage.output_tokens,
                }
        except Exception as e:
            logger.error(f"Error generating post content: {str(e)}")
            raise HTTPException(status_code=500, detail="Error generating post content.")

        # Generate the tagline
        try:
            tagline_prompt = build_prompt_tagline(item, post_content)
            logger.info(f"Generating tagline with prompt: {tagline_prompt}")
            tagline = fetch_response(tagline_prompt, "claude-3-5-sonnet-20241022").content[0].text.strip()

            # Check if tagline violates policies
            if tagline == FALLBACK_MESSAGE or await is_content_explicit(tagline):
                logger.warning("Explicit or fallback content detected in tagline")
                return {
                    "post": post_content,
                    "tagline": FALLBACK_MESSAGE,
                    "image_url": PREBUILT_IMAGE_URL,
                    "input_tokens": post.usage.input_tokens,
                    "output_tokens": post.usage.output_tokens,
                }
        except Exception as e:
            logger.error(f"Error generating tagline: {str(e)}")
            raise HTTPException(status_code=500, detail="Error generating tagline.")

        # Generate dynamic image
        try:
            image_model = "ultra"
            image_prompt_dynamic = build_dynamic_image_prompt(post_content, item.style, colors)
            logger.info(f"Generating image with prompt: {image_prompt_dynamic}")
            image_prompt = fetch_response(image_prompt_dynamic, "claude-3-5-sonnet-20241022").content[0].text
            image = fetch_image_response(image_prompt, image_model)

            # Style adjustments and overlays
            image_style = generate_random_hex_color() if not item.style or "vibrant color theme" in item.style else item.style.split(",")[0].strip()
            text_image = add_text_overlay(image, tagline, image_style)
            final_image_bytes = overlay_logo(text_image, logo_bytes)

            # Upload image to S3
            image_name = f"gen_post_{uuid.uuid4().hex}.jpeg"
            upload_image_to_s3(final_image_bytes, image_name)
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"
        except Exception as e:
            logger.error(f"Error generating or uploading image: {str(e)}")
            raise HTTPException(status_code=500, detail="Error generating or uploading image.")

        # Return the final result
        return {
            "post": post_content,
            "tagline": tagline,
            "image_url": s3_url,
            "input_tokens": post.usage.input_tokens,
            "output_tokens": post.usage.output_tokens,
        }

    except StyleValidationError as e:
        logger.error(f"Style validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An internal error occurred.")
