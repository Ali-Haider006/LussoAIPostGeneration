import requests
import os
from dotenv import load_dotenv
load_dotenv()
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")

response = requests.post(
    f"https://api.stability.ai/v2beta/stable-image/generate/ultra",
    headers={
        "authorization": f"Bearer {STABILITY_API_KEY}",
        "accept": "image/*"
    },
    files={"none": ''},
    data={
        "prompt": "studio medium portrait of Brad Pitt waving his hands, detailed, film, studio lighting, 90mm lens, by Martin Schoeller:6 | disfigured, deformed hands, blurry, grainy, broken, cross-eyed, undead, photoshopped, overexposed, underexposed, low-res, bad anatomy, bad hands, extra digits, fewer digits, bad digit, bad ears, bad eyes, bad face, cropped: -5",
        "output_format": "jpeg",
    },
)

if response.status_code == 200:
    with open("./bardpit_goodsd3.jpeg", 'wb') as file:
        file.write(response.content)
else:
    raise Exception(str(response.json()))