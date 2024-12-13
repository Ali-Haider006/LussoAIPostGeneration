from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
)

class Item(BaseModel):
    smapp: str
    length: int 
    bzname: str
    purpose: str
    targetAudience: str 
    preferredTone: str
    website: str
    hashtags: bool
    model: str

def fetch_response(prompt, model):
    try:
        post = client.messages.create(
            # claude-3-5-sonnet-20241022
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
        # if post.error:
        #     print("An error occurred while making the request")
        #     raise
        return post.content
    except:
        print("An error occurred while making the request")
        raise

@app.post("/api/generate-post")
async def generate_post(item: Item):
    # sometimes haulicinates for in website shoping as website is gentting mentioned otherwise good
    # without hashtags: Generate a polished social media post for {item.smapp}, approximately {item.length} words long. The post is for the business {item.bzname} and aims to {item.purpose}, targeting {item.targetAudience}. Use a {item.preferredTone} tone and incorporate only the provided information. Do not include hashtags, meta-comments, or fabricated details. The business website is {item.website}. Focus solely on the provided information to create a professional and publishable post.
    # with hashtags: Generate a polished social media post for {item.smapp}, approximately {item.length} words long. The post is for the business {item.bzname} and aims to {item.purpose}, targeting {item.targetAudience}. Use a {item.preferredTone} tone and incorporate only the provided information. Include a few relevant and creative hashtags for better visibility. The business website is {item.website}. Avoid adding extra commentary or fabricated details.
    prompt = f"Write a professional social media post for {item.smapp}, about {item.length} words long, for the business {item.bzname}. The post should achieve the goal: {item.purpose}, targeting {item.targetAudience}, and using a {item.preferredTone} tone. Use the website {item.website} naturally. Donot include any introductory or opening or ending or closing text and do not include hashtags."
    if item.hashtags:
        prompt = f"Write a professional social media post for {item.smapp}, about {item.length} words long, for the business {item.bzname}. The post should achieve the goal: {item.purpose}, targeting {item.targetAudience}, and using a {item.preferredTone} tone. Use the website {item.website} naturally and include relevant hashtags. Donot include any introductory or opening or ending or closing text."
    
    # TODO: Moderation for prompt to be added

    try:
        post = fetch_response(prompt, item.model)
        return {"post": post}
    except:
       raise HTTPException(status_code=400, detail = "Unable to generate post") 

@app.get("/test")
async def root():
    return {"message": "Server running"}
