from fastapi import HTTPException
import anthropic
from app.core.config import ANTHROPIC_API_KEY, STABILITY_API_KEY
from app.core.logger import logger
import requests

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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
