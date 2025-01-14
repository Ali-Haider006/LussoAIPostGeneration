from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from app.models.item import Item
from app.services.prompt_building import build_prompt_bulk_generation, build_prompt_tagline, build_topics_gen_prompt
from app.services.api_calls import fetch_response, fetch_image_response
from app.services.image_processing import overlay_logo, add_text_overlay, generate_random_hex_color
from app.services.text_processing import find_all_texts
from typing_extensions import Annotated, Optional
from app.utils.download_image_from_url import download_image_from_url
from app.core.logger import logger
import uuid
from app.services.prompt_building import build_dynamic_image_prompt
from app.services.s3 import upload_image_to_s3, BUCKET_NAME
import json

router = APIRouter()

@router.post("/bulk-generate-post")
async def bulk_generate_post(
    length: Annotated[int, Form(..., ge=10, le=700)] = 150,
    bzname: str = Form(...),
    preferredTone: str = Form(...),
    website: str = Form(...),
    hashtags: bool = Form(...),
    color_theme: Optional[str] = Form(None),
    number_of_posts: Annotated[int, Form(..., ge=1, le=30)] = 10,
    logo: str = Form(...),
    posts: str = Form(...),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"
):
    item = Item(
        length=length,
        bzname=bzname,
        purpose="",
        preferredTone=preferredTone,
        website=website,
        hashtags=hashtags,
        color_theme=color_theme if color_theme else "vibrant color theme",
        model=model
    )

    posts = json.loads(posts)
    posts_text = find_all_texts(posts, number_of_posts)
    prompt = build_topics_gen_prompt(posts_text, number_of_posts)
    logger.info(f"Generating topics with prompt: {prompt}")
    input_tokens, output_tokens = 0, 0
    try:
        topics_res = fetch_response(prompt, model)
        input_tokens += topics_res.usage.input_tokens
        output_tokens += topics_res.usage.output_tokens
        topics = json.loads(topics_res.content[0].text)
        posts = []
        logo_bytes = await download_image_from_url(logo)

        for topic in topics["topics"]:
            item.purpose = topic
            prompt = build_prompt_bulk_generation(item)
            logger.info(f"Generating post with prompt: {prompt}")
            post_res = fetch_response(prompt, item.model)
            input_tokens += post_res.usage.input_tokens
            output_tokens += post_res.usage.output_tokens

            tagline_prompt = build_prompt_tagline(item, post_res.content[0].text)
            logger.info(f"Generating tagline with prompt: {tagline_prompt}")
            
            tagline = fetch_response(tagline_prompt, "claude-3-5-sonnet-20241022").content[0].text
            logger.info(f"Generated tagline: {tagline}")

            image_model = "ultra"
            image_prompt_dynamic = build_dynamic_image_prompt(post_res.content[0].text, item.color_theme)

            image_prompt = fetch_response(image_prompt_dynamic, "claude-3-5-sonnet-20241022").content[0].text

            logger.info(f"Generated image prompt: {image_prompt}")

            image = fetch_image_response(image_prompt, image_model)

            if not item.color_theme or item.color_theme == "vibrant color theme" or "#" not in item.color_theme:
                image_color_theme = generate_random_hex_color()
            else:
                image_color_theme = item.color_theme.split(",")[0].strip()

            text_image = add_text_overlay(image, tagline, image_color_theme)

            final_image_bytes = overlay_logo(text_image, logo_bytes)

            # Generate unique image name
            image_name = f"gen_post_{uuid.uuid4().hex}.jpeg"
            # Upload image to S3
            upload_image_to_s3(final_image_bytes, image_name) 
            # Generate S3 URL
            s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"

            posts.append({
                "topic": topic, 
                "post": post_res.content[0].text,
                "tagline": tagline,
                "image_url": s3_url,	
            })

            # image_name = f"./imagesp3/gen_post_{post_res.id}.jpeg"
            # with open(image_name, 'wb') as file:
            #     file.write(final_image_bytes)
            #     file.close()
            
        
        return {
            "posts": posts,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate post")
