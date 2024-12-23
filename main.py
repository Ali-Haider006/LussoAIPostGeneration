# No Third person except AI-Team is allowed to run this code. No changes in this code are allowed except by approval from AI Team
# Moderation API will be implemented once This application will be in production.

from fastapi import FastAPI, HTTPException, Form, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, root_validator, ValidationError
from typing_extensions import Annotated, Optional
import anthropic
import os
from dotenv import load_dotenv
import logging
import requests
import base64
# from PIL import Image
# import rembg

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
    length: Annotated[int, Field(strict=True, ge=10, le=700)] = 150  # Ensure word length is reasonable
    bzname: str
    purpose: str 
    preferredTone: str
    website: str  
    hashtags: bool
    color_theme: str
    model: Annotated[str, Field(min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"  # Default model value

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
    model: Annotated[str, Field(min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"

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

def build_image_prompt(item: Item, tagline: str) -> str:
    refined_prompt = (
        f"Create a high-quality, professional social media advertisement poster for the following product: "
        f"Brand Name: '{item.bzname}' and Product Description: '{tagline}'. "
        f"The design should use the exact color palette: {item.color_theme}. "
        f"Strictly include only the following text in the image: '{item.bzname}' and '{tagline}'. "
        "No extra text, watermarks, or unrelated elements should appear in the image. "
        "Focus on a clean, minimalistic design with a professional, modern aesthetic. "
        "Use balanced typography, harmonious color integration, and a visually appealing layout to create a striking advertisement."
    )
    return refined_prompt

def build_static_image_prompt(post_content: str, tagline: str, bzname: str, color_theme: str) -> str:
    return (
        f"Professional {color_theme} advertisement: {post_content}. "
        f"Modern minimalist design with '{bzname}' in bold {color_theme} text, centered. "
        f"Below, '{tagline}' in clean typography. "
        "Elegant composition, balanced layout, 8K quality, commercial photography style. "
        "Sharp text, high contrast, professional lighting."
    )

def build_dynamic_image_prompt(post_content: str, tagline: str, color_theme: str) -> str:
    return (
        f"Generate a prompt for a high-quality, visually appealing social media advertisement image. "
        f"Ask to strictly include only the following text in the image the tagline: '{tagline}', and ask the model it should be visually distinct, engaging, and a central part of the design. "
        f"Tagline is must and should be in the image no matter what and prompt should put every emphasis on including tagline this tagline in image: '{tagline}' in generated image. "
        f"Focus on the content theme: '{post_content}' to ensure the image aligns with the overall message. "
        f"Use the color theme: {color_theme} as the primary palette, ensuring the colors dominate the design while remaining harmonious and professional. "
        "The design must prioritize the business name and tagline as key visual elements, integrating them seamlessly into the layout. "
        "Ask not to include extra text, watermarks, or unrelated elements in the image. "
        "Describe specific visual elements and composition, emphasizing balance, modern aesthetics, and alignment with the provided text. "
        "While generating prompt keep in mind all the knowledge you have about prompt engineering and specially prompt engineering for image generation models. "
        "Use techniques like quality boosters, weighted terms, style modifiers and other prompt engineering techniques. "
        "Do not include any introductory or opening or ending or closing text; provide only the prompt needed for generating the advertisement image."
    )

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

def fetch_image_response(image_prompt: str, model: str):
    try:
        response = requests.post(
            f"https://api.stability.ai/v2beta/stable-image/generate/{model}",
            headers={
                "authorization": f"Bearer {STABILITY_API_KEY}",
                "accept": "image/*"
            },
            files={"none": ''},
            data={
                "prompt": image_prompt,
                "output_format": "jpeg",
            },
        )
        if response.status_code == 200:
            return response.content
        raise HTTPException(status_code=response.status_code, detail="Unable to generate image") 
    except HTTPException as http_exc:
        raise http_exc


# Change the endpoints to accept form-data
@app.post("/api/generate-post")
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

        image_prompt = fetch_response(image_prompt_dynamic, item.model).content[0].text
        # image_prompt = build_static_image_prompt(post.content[0].text, tagline, item.bzname, item.color_theme)

        logger.info(f"Generated image prompt: {image_prompt}")

        image = fetch_image_response(image_prompt, image_model)
        image_base64 = base64.b64encode(image).decode('utf-8')
        # Save the image to a file for testing
        with open("./gen_post_2.jpeg", 'wb') as file:
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

#Regeneration Endpoint Update
@app.post("/api/regenerate-post")
async def regenerate_post(
    post: str = Form(...),
    suggestion: Optional[str] = Form(None),
    model: Annotated[str, Form(..., min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"
):
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

@app.get("/test")
async def test_endpoint():
    return {"message": "Server is running"}
