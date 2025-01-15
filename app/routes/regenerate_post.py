from fastapi import APIRouter, HTTPException, Form, status
from typing_extensions import Annotated, Optional
from typing import Dict, Union
import uuid
import traceback

from app.models.regeneration_item import RegenerationItem
from app.services.prompt_building import build_prompt_regeneration
from app.services.api_calls import fetch_response
from app.core.logger import logger

router = APIRouter()

def validate_inputs(
    post: str,
    count: int,
    model: str
) -> None:
    """Validate input parameters before processing."""
    if not post.strip():
        raise ValueError("Post content cannot be empty")
    
    if count < 0:
        raise ValueError("Count cannot be negative")
        
    if count >= 2:
        raise ValueError("Cannot regenerate more than 2 times")
    
    supported_models = {
        "claude-3-5-haiku-20241022",
        "claude-3-5-sonnet-20241022",
    }

    if model not in supported_models:
        raise ValueError(f"Unsupported model. Must be one of: {', '.join(supported_models)}")

def validate_api_response(response) -> None:
    """Validate the API response structure."""
    if not response or not response.content:
        raise ValueError("Empty response from API")
    if not response.usage or not hasattr(response.usage, 'input_tokens') or not hasattr(response.usage, 'output_tokens'):
        raise ValueError("Invalid token usage information in response")

@router.post("/regenerate-post", response_model=Dict[str, Union[str, int]])
async def regenerate_post(
    post: str = Form(...),
    suggestion: Optional[str] = Form(None),
    count: int = Form(...),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022",
) -> Dict[str, Union[str, int]]:
    """
    Regenerate a post using AI model based on input parameters.
    
    Args:
        post (str): Original post content
        suggestion (str, optional): Suggestion for regeneration
        count (int): Number of regeneration attempts
        model (str): AI model to use
        
    Returns:
        Dict[str, Union[str, int]]: Dictionary containing regenerated post and token usage
        
    Raises:
        HTTPException: Various exceptions based on the error type
    """
    request_id = str(uuid.uuid4())
    logger.info("Starting post regeneration request", extra={
        "request_id": request_id,
        "model": model,
        "regeneration_count": count,
        "has_suggestion": bool(suggestion)
    })
    
    try:
        # Validate inputs
        validate_inputs(post, count, model)
        
        # Initialize regeneration item
        item = RegenerationItem(
            post=post,
            suggestion=suggestion,
            model=model
        )
        
        # Build and log prompt
        logger.debug("Building regeneration prompt", extra={"request_id": request_id})
        prompt = build_prompt_regeneration(item)
        logger.info("Generated prompt for regeneration", extra={
            "request_id": request_id,
            "prompt_length": len(prompt)
        })
        
        # Make API call
        logger.debug("Making API call", extra={
            "request_id": request_id,
            "model": model
        })
        response = fetch_response(prompt, item.model)
        
        # Validate response
        validate_api_response(response)
        
        regenerated_post = response.content[0].text
        logger.info("Successfully regenerated post", extra={
            "request_id": request_id,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "response_length": len(regenerated_post)
        })
        
        return {
            "post": regenerated_post,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
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
            "request_id": request_id,
            "model": model
        })
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=error_msg
        )
    
    except HTTPException as http_exc:
        logger.error("HTTP exception occurred", extra={
            "request_id": request_id,
            "status_code": http_exc.status_code,
            "detail": http_exc.detail
        })
        raise http_exc
        
    except Exception as e:
        error_msg = "An unexpected error occurred while regenerating the post"
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