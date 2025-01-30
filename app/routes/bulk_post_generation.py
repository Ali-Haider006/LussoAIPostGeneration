from fastapi import APIRouter, HTTPException, Form, WebSocket, Depends, WebSocketDisconnect
from app.models.bulk_item import BulkItem
import io
from PIL import Image
from app.services.image_processing import extract_color_proportions
from app.services.prompt_building import build_prompt_bulk_generation, build_prompt_tagline_no_purpose, build_topics_gen_prompt, build_prompt_font_selection
from app.services.api_calls import fetch_response, fetch_image_response
from app.services.image_processing import overlay_logo, add_text_overlay
from app.services.text_processing import get_post_facebook, get_posts_linkedIn, get_text_business
from app.utils.download_image_from_url import download_image_from_url
from app.core.logger import logger
import uuid
from app.services.prompt_building import build_dynamic_image_prompt
from app.services.s3 import upload_image_to_s3, BUCKET_NAME
import json
import asyncio
from app.sockets.websocket_manager import manager
from typing import Dict, List
from app.utils.constants import FONT_LIST
from app.utils.validate_font import get_valid_font

router = APIRouter()

async def process_single_post(
    topic: str,
    item: BulkItem,
    logo_bytes: bytes,
    output_image: Image.Image,
    color_proportions: List[dict],
    model: str
) -> dict:
    """Process a single post generation with all required steps."""
    try:
        colors = ", ".join([sub['colorCode'] for sub in color_proportions])
        item.purpose = topic
        
        # Generate post content
        prompt = build_prompt_bulk_generation(item)
        post_res = fetch_response(prompt, item.model)
        
        # Generate tagline
        tagline_prompt = build_prompt_tagline_no_purpose(item, post_res.content[0].text)
        tagline = fetch_response(tagline_prompt, "claude-3-5-sonnet-20241022").content[0].text
        
        # Generate and process image
        image_prompt_dynamic = build_dynamic_image_prompt(post_res.content[0].text, item.style, colors)
        image_prompt = fetch_response(image_prompt_dynamic, "claude-3-5-sonnet-20241022").content[0].text
        image = fetch_image_response(image_prompt, "ultra")

        font_prompt = build_prompt_font_selection(item, tagline, FONT_LIST)

        logger.info(f"Generated font prompt: {font_prompt}")

        model_font = fetch_response(font_prompt, item.model)

        font = get_valid_font(model_font.content[0].text, FONT_LIST)

        logger.info(f"Generated font: {font}")
        
        # Process image with overlays
        text_image = add_text_overlay(image, tagline, "test", font)
        final_image_bytes = overlay_logo(text_image, logo_bytes)
        
        # Upload to S3
        image_name = f"gen_post_{uuid.uuid4().hex}.jpeg"
        await upload_image_to_s3(final_image_bytes, image_name)
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_name}"
        
        return {
            "topic": topic,
            "post": post_res.content[0].text,
            "tagline": tagline,
            "image_url": s3_url,
        }
    except Exception as e:
        logger.error(f"Error processing post for topic '{topic}': {str(e)}")
        raise

@router.websocket("/ws/bulk-generate/{client_id}")
async def bulk_post_generation(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data) if isinstance(raw_data, str) else json.loads(json.dumps(raw_data))
            except json.JSONDecodeError as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Invalid JSON format: {str(e)}"
                }))
                continue

            # Extract business description
            business_description = data.get("businessDescription", {})
            facebook_posts = data.get("facebookPosts", {})
            linkedin_posts = data.get("linkedInPosts", {})
            business_text = get_text_business(business_description)

            try:
                item = BulkItem(
                    length=data.get("length", 150),
                    bzname=data.get("bzname", ""), 
                    purpose="",
                    preferredTone=data.get("preferredTone", ""),
                    website=data.get("website", ""),
                    hashtags=data.get("hashtags", False),
                    style=data.get("style", "digital"),
                    model=data.get("model", "claude-3-5-haiku-20241022")
                )
            except ValidationError as e:
                error_messages = []
                for error in e.errors():
                    field = error["loc"][0]
                    msg = error["msg"]
                    error_messages.append(f"{field}: {msg}")
                
                formatted_error = {
                    "type": "validation_error",
                    "errors": error_messages,
                    "message": "Validation failed for the following fields: " + ", ".join(error_messages)
                }
                await manager.send_error(client_id, json.dumps(formatted_error))
                continue
            except Exception as e:
                await manager.send_error(client_id, f"Unexpected error during validation: {str(e)}")
                continue

            number_of_posts = min(max(data.get("number_of_posts", 10), 1), 30)

            # Process posts data
            posts_text = []
            if facebook_posts.get("payload"):
                posts_facebook = get_post_facebook(facebook_posts["payload"], number_of_posts)
                posts_text = posts_facebook
            if linkedin_posts.get("payload"):
                posts_linkedin = get_posts_linkedIn(linkedin_posts["payload"], number_of_posts)
                if len(posts_linkedin) > len(posts_text):
                    posts_text = posts_linkedin

            # Generate topics
            try:
                prompt = build_topics_gen_prompt(posts_text, business_text, number_of_posts)
                topics_res = fetch_response(prompt, item.model)
                topics_data = topics_res.content[0].text
                if isinstance(topics_data, str):
                    topics = json.loads(topics_data)["topics"]
                else:
                    topics = topics_data["topics"]            
                
            except Exception as e:
                await manager.send_error(client_id, f"Error generating topics: {str(e)}")
                continue

            # Process logo
            try:
                logo_bytes = await download_image_from_url(data["logo"])
                output_image = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
                color_proportions = extract_color_proportions(output_image)
            except Exception as e:
                await manager.send_error(client_id, f"Error processing logo: {str(e)}")
                continue

            # Process posts with progress updates
            posts = []
            for idx, topic in enumerate(topics, 1):
                try:
                    post_data = await process_single_post(
                        topic, item, logo_bytes, output_image, 
                        color_proportions, item.model
                    )
                    posts.append(post_data)
                    progress_message = {
                            "type": "progress",
                            "current": idx,
                            "total": number_of_posts,
                            "post_data": post_data
                        }
                    await websocket.send_text(json.dumps(progress_message))

                except Exception as e:
                    await manager.send_error(client_id, f"Error processing post {idx}: {str(e)}")
                    logger.error(f"Error processing post {idx}: {str(e)}")
                    continue

                await asyncio.sleep(0.1)

            # Send completion message
            completion_message = {
                    "type": "complete",
                    "posts": posts
                }
            await websocket.send_text(json.dumps(completion_message))

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {traceback.format_exc()}")
        await manager.send_error(client_id, f"An unexpected error occurred: {str(e)}")
        manager.disconnect(client_id)