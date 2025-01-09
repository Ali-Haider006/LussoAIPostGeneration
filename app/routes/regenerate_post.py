from fastapi import APIRouter, HTTPException, Form
from app.models.regeneration_item import RegenerationItem
from app.services.prompt_building import build_prompt_regeneration
from app.services.api_calls import fetch_response
from typing_extensions import Annotated, Optional
from app.core.logger import logger

router = APIRouter()

@router.post("/regenerate-post")
async def regenerate_post(
    post: str = Form(...),
    suggestion: Optional[str] = Form(None),
    count: int = Form(...),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"
):
    if count >= 2:
        raise HTTPException(status_code=403, detail="Cannot regenerate more than 2 times")
    item = RegenerationItem(post=post, suggestion=suggestion, model=model)
    prompt = build_prompt_regeneration(item)
    logger.info(f"Regenerating post with prompt: {prompt}")
    try:
        post = fetch_response(prompt, item.model)
        return {
            "post": post.content[0].text, 
            "input_tokens": post.usage.input_tokens,
            "output_tokens": post.usage.output_tokens,    
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to regenerate post")
