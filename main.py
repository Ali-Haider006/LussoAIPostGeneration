# No Third person except AI-Team is allowed to run this code. No changes in this code are allowed except by approval from AI Team
#Moderation API will be implemented once This application will be in production.
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing_extensions import Annotated
import anthropic
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    logger.error("ANTHROPIC_API_KEY not found in environment variables.")
    raise ValueError("ANTHROPIC_API_KEY is required")

try:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Anthropics client: {e}")
    raise

origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    length: Annotated[int, Field(strict=True, ge=10, le=700)]  # Ensure word length is reasonable
    bzname: str
    purpose: str
    targetAudience: str
    preferredTone: str
    website: str  
    hashtags: bool
    model: str

class RegenerationItem(BaseModel):
    post: str
    suggestion: str
    length: Annotated[int, Field(strict=True, ge=10, le=700)]  # Ensure word length is reasonable
    bzname: str
    purpose: str
    targetAudience: str
    preferredTone: str
    website: str  
    model: str

def build_prompt_generation(item: Item) -> str:
    base_prompt = (
        f"Write a professional social media post, about {item.length} words long, "
        f"for the business {item.bzname}. The post should achieve the goal: {item.purpose}, targeting {item.targetAudience}, "
        f"and using a {item.preferredTone} tone. Use the website {item.website} naturally."
    )
    if item.hashtags:
        return base_prompt + " Include relevant hashtags. Do not include any introductory or opening or ending or closing text."
    return base_prompt + " Do not include hashtags. Do not include any introductory or opening or ending or closing text."

def build_prompt_regeneration(item: RegenerationItem) -> str:
    return (
        f"Rewrite and improve the social media post, about {item.length} words long, for the business {item.bzname}.",
        f"The post aims to achieve: {item.purpose}, targeting {item.targetAudience}, and using a {item.preferredTone} tone. The business website is {item.website}",
        f"Here is the previous post:{item.post}",
        f"Feedback or suggestion for improvement: {item.suggestion}",
        f"Regenerate the post based on this feedback while ensuring it adheres to the original instructions and aligns with the given purpose, target audience, and tone.",
    )

def fetch_response(prompt: str, model: str) -> str:
    try:
        response = client.messages.create(
            model=model,
            system="You are a professional social media content creator. Your job is to create posts that strictly adhere to the given instructions and data. Avoid assumptions or additions like promotions, comparisons, or any phrases not explicitly mentioned in the input. Your output must be polished, factual, and directly publishable. Use only the provided information and omit any unnecessary details or speculative content.",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )
        if hasattr(response, "error") and response.error:
            logger.error(f"Anthropic API error: {response.error}")
            raise ValueError("Error in API response")
        return response.content
    except Exception as e:
        logger.error(f"Error while fetching response: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/api/generate-post")
async def generate_post(item: Item):
    prompt = build_prompt_generation(item)
    logger.info(f"Generating post with prompt: {prompt}")
    try:
        post = fetch_response(prompt, item.model)
        return {"post": post}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate post")
    
@app.post("/api/regenerate-post")
async def regenerate_post(item: Item):
    prompt = build_prompt_regeneration(item)
    logger.info(f"Regenerating post with prompt: {prompt}")
    try:
        post = fetch_response(prompt, item.model)
        return {"post": post}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to regenerate post")

@app.get("/test")
async def test_endpoint():
    return {"message": "Server is running"}
