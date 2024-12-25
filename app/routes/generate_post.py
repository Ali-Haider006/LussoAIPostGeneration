from fastapi import APIRouter, HTTPException, Form
from app.models.item import Item
from app.services.prompt_building import build_prompt_generation, build_prompt_tagline
from app.services.api_calls import fetch_response, fetch_image_response
from typing_extensions import Annotated, Optional
from app.core.logger import logger
import base64
from app.services.prompt_building import build_dynamic_image_prompt

router = APIRouter()

@router.post("/generate-post")
async def generate_post(
    length: Annotated[int, Form(..., ge=10, le=700)] = 150,
    bzname: str = Form(...),
    purpose: str = Form(...),
    preferredTone: str = Form(...),
    website: str = Form(...),
    hashtags: bool = Form(...),
    color_theme: str = Form(...),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"
):
    item = Item(
        length=length,
        bzname=bzname,
        purpose=purpose,
        preferredTone=preferredTone,
        website=website,
        hashtags=hashtags,
        color_theme=color_theme,
        model=model
    )
    prompt = build_prompt_generation(item)
    logger.info(f"Generating post with prompt: {prompt}")
    try:
        post = fetch_response(prompt, item.model)

        tagline_prompt = build_prompt_tagline(item, post.content[0].text)
        logger.info(f"Generating tagline with prompt: {tagline_prompt}")
        
        tagline = fetch_response(tagline_prompt, item.model).content[0].text
        logger.info(f"Generated tagline: {tagline}")
        
        image_model = "ultra"
        image_prompt_dynamic = build_dynamic_image_prompt(post.content[0].text, tagline, item.color_theme)

        image_prompt = fetch_response(image_prompt_dynamic, "claude-3-5-sonnet-20241022").content[0].text
        # image_prompt = build_static_image_prompt(post.content[0].text, tagline, item.bzname, item.color_theme)

        logger.info(f"Generated image prompt: {image_prompt}")

        image = fetch_image_response(image_prompt, image_model)
        image_base64 = base64.b64encode(image).decode('utf-8')
        # Save the image to a file for testing
        with open("./gen_post_7.jpeg", 'wb') as file:
            file.write(image)
        return {
            "post": post.content[0].text, 
            "tagline": tagline,
            "image": image_base64,	
            "input_tokens": post.usage.input_tokens,
            "output_tokens": post.usage.output_tokens,    
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate post")
