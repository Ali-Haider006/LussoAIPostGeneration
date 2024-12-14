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
    smapp: str
    length: Annotated[int, Field(strict=True, ge=10, le=700)]  # Ensure word length is reasonable
    bzname: str
    purpose: str
    targetAudience: str
    preferredTone: str
    website: str  
    hashtags: bool
    model: str

def build_prompt(item: Item) -> str:
    base_prompt = (
        f"Write a professional social media post for {item.smapp}, about {item.length} words long, "
        f"for the business {item.bzname}. The post should achieve the goal: {item.purpose}, targeting {item.targetAudience}, "
        f"and using a {item.preferredTone} tone. Use the website {item.website} naturally."
    )
    if item.hashtags:
        return base_prompt + " Include relevant hashtags. Donot include any introductory or opening or ending or closing text."
    return base_prompt + " Do not include hashtags. Donot include any introductory or opening or ending or closing text."

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
    prompt = build_prompt(item)
    logger.info(f"Generating post with prompt: {prompt}")
    try:
        post = fetch_response(prompt, item.model)
        return {"post": post}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate post")

@app.get("/test")
async def test_endpoint():
    return {"message": "Server is running"}
