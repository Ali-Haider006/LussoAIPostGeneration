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
from app.utils.constants import FONT_LIST
from app.services.prompt_building import build_prompt_font_selection
from app.utils.validate_font import get_valid_font
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
    style: str= Form(...),
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
        try:
            logo_bytes = await download_image_from_url(logo)
            output_image = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

            color_proportions = extract_color_proportions(output_image)
            colors = ", ".join([ sub['colorCode'] for sub in color_proportions ])

            prompt = build_prompt_generation(item)
            logger.info(f"Generating post with prompt: {prompt}")

            post = fetch_response(prompt, item.model)

            tagline_prompt = build_prompt_tagline(item, post.content[0].text)
            logger.info(f"Generating tagline with prompt: {tagline_prompt}")
            
            tagline = fetch_response(tagline_prompt, "claude-3-5-sonnet-20241022").content[0].text
            logger.info(f"Generated tagline: {tagline}")
            
            image_model = "ultra"
            image_prompt_dynamic = build_dynamic_image_prompt(post.content[0].text, item.style, colors)

            image_prompt = fetch_response(image_prompt_dynamic, "claude-3-5-sonnet-20241022").content[0].text

            logger.info(f"Generated image prompt: {image_prompt}")

            image = fetch_image_response(image_prompt, image_model)

            if not item.style or item.style == "vibrant color theme" or "#" not in item.style:
                image_style = generate_random_hex_color()
            else:
                image_style = item.style.split(",")[0].strip()
            
            font_prompt = build_prompt_font_selection(item, tagline, FONT_LIST)

            logger.info(f"Generated font prompt: {font_prompt}")

            model_font = fetch_response(font_prompt, item.model)

            font = get_valid_font(model_font.content[0].text, FONT_LIST)

            logger.info(f"Generated font: {font}")

            text_image = add_text_overlay(image, tagline, image_style, font)

            final_image_bytes = overlay_logo(text_image, logo_bytes)

            # Generate unique image name
            image_name = f"gen_post_{uuid.uuid4().hex}.jpeg"
            # Upload image to S3
            await upload_image_to_s3(final_image_bytes, image_name) 
            # Generate S3 URL
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"

            return {
                "post": post.content[0].text, 
                "tagline": tagline,
                "image_url": s3_url,  # Return the S3 URL instead of Base64
                "input_tokens": post.usage.input_tokens,
                "output_tokens": post.usage.output_tokens,    
            }
        
        except HTTPException as http_exc:
            logger.warning(f"HTTP exception: {http_exc.detail}")
            raise HTTPException(status_code=400, detail="HTTP exception")
        except ValueError as val_err:
            logger.error(f"Value error encountered: {val_err}")
            raise HTTPException(status_code=400, detail="Invalid input data")
        except Exception as e:
            logger.error(f"Unhandled error: {e}")
            logger.debug(traceback.format_exc())
            raise HTTPException(status_code=500, detail="An internal error occurred while generating posts.")
    
    except StyleValidationError as e:
        logger.error(f"Style validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail="An internal error occurred while processing request")