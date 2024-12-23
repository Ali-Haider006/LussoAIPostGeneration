# No Third person except AI-Team is allowed to run this code. No changes in this code are allowed except by approval from AI Team
#Moderation API will be implemented once This application will be in production.
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, root_validator, ValidationError
from typing_extensions import Annotated, Optional
import anthropic
import os
from dotenv import load_dotenv
import logging
import requests

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")
if not ANTHROPIC_API_KEY or not STABILITY_API_KEY:
    logger.error("ANTHROPIC_API_KEY or STABILITY_API_KEY not found in environment variables.")
    raise ValueError("ANTHROPIC_API_KEY and STABILITY_API_KEY is required")

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
    preferredTone: str
    website: str  
    hashtags: bool
    model: str

    @root_validator(pre=True)
    def validate_purpose(cls, values):
        purpose = values.get("purpose")
        if purpose and len(purpose.split()) < 10:
            raise ValueError("Purpose must be at least 10 words long.")
        return values

# Updated Schema for Regeneration
class RegenerationItem(BaseModel):
    post: str
    suggestion: Optional[str] = None 
    model: str

def build_prompt_generation(item: Item) -> str:
    base_prompt = (
        f"Write a professional social media post, about {item.length} words long, "
        f"for the business {item.bzname}. The post should achieve the goal: {item.purpose}, "
        f"and using a {item.preferredTone} tone. Use the website {item.website} naturally. "
    )
    if item.hashtags:
        return base_prompt + "Include relevant hashtags. Do not include any introductory or opening or ending or closing text."
    return base_prompt + "Do not include hashtags. Do not include any introductory or opening or ending or closing text."

def build_prompt_tagline(item: Item, post: str) -> str:
    base_prompt = (
        f"Write a professional tagline for the post {post}, maximum 6 words long, "
        f"and using a {item.preferredTone} tone. "
    )
    return base_prompt + "Do not include any introductory or opening or ending or closing text."

#Prompt Engineering According to Figma Design
def build_prompt_regeneration(item: RegenerationItem) -> str:
    base_prompt = (
        f"Rewrite and improve the social media post, "
        f"Here is the previous post:{item.post}, "
    )

    if item.suggestion:
        base_prompt += f"Feedback or suggestion for improvement: {item.suggestion}. "
    else:
        base_prompt += "Improve the post generally by enhancing creativity, clarity, and engagement. "

    return base_prompt + "Regenerate the post based on this feedback while ensuring it adheres to the original instructions and aligns with the given purpose, and tone. Do not include any introductory or opening or ending or closing text just give me post text that can be directly posted."

def fetch_response(prompt: str, model: str) -> str:
    try:
        response = client.messages.create(
            model=model,
            system="You are a professional social media content creator. Your job is to create posts that strictly adhere to the given instructions and data. Avoid assumptions or additions like promotions, comparisons, or any phrases not explicitly mentioned in the input. Your output must be polished, factual, and directly publishable. Use only the provided information and omit any unnecessary details or speculative content.",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )
        if hasattr(response, "error") and response.error:
            logger.error(f"Anthropic API error: {response.error}")
            raise ValueError("Error in API response")
        return response
    except Exception as e:
        logger.error(f"Error while fetching response: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
def build_image_prompt(item: Item, tagline: str) -> str:
    refined_prompt = (
        f"Design an eye-catching, modern social media advertisement poster for a product. "
        f"Brand Name: '{item.bzname}' should be very visible and stand out. "
        f"Product Description: '{tagline}', emphasizing the product's unique features. "
        "Generate a compelling, catchy tagline that appeals to the audience and aligns with the brand's voice. "
        "The ad should feature a clean, minimalistic layout with balanced colors and typography that conveys professionalism and high quality. "
        "Ensure the design is engaging, with the brand name prominently displayed, the tagline capturing attention, and the overall style modern and visually striking."
    )
    return refined_prompt

def fetch_image_response(item: Item, tagline: str, model: str):
    try:
        response = requests.post(
            f"https://api.stability.ai/v2beta/stable-image/generate/{model}",
            headers={
                "authorization": f"Bearer {STABILITY_API_KEY}",
                "accept": "image/*"
            },
            files={"none": ''},
            data={
                "prompt": build_image_prompt(item, tagline),
                "output_format": "jpeg",
            },
        )
        if response.status_code == 200:
            return response.content
        raise HTTPException(status_code=500, detail="Unable to generate image") 
    except HTTPException as http_exc:
        raise http_exc


@app.post("/api/generate-post")
async def generate_post(item: Item):
    prompt = build_prompt_generation(item)
    logger.info(f"Generating post with prompt: {prompt}")
    try:
        post = fetch_response(prompt, item.model)
        image_model = "ultra"
        tagline = ""
        image = fetch_image_response(item, tagline, image_model)
        return {
            "post": post.content, 
            "input_tokens": post.usage.input_tokens,
            "output_tokens": post.usage.output_tokens,    
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate post")
    

 #Regeneration Definition Updated   
@app.post("/api/regenerate-post")
async def regenerate_post(item: RegenerationItem):
    prompt = build_prompt_regeneration(item)
    logger.info(f"Regenerating post with prompt: {prompt}")
    try:
        post = fetch_response(prompt, item.model)
        return {
            "post": post.content, 
            "input_tokens": post.usage.input_tokens,
            "output_tokens": post.usage.output_tokens,    
        }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Unable to regenerate post")

@app.get("/test")
async def test_endpoint():
    return {"message": "Server is running"}
