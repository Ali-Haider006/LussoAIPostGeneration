import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION_NAME = os.getenv("AWS_REGION_NAME")
BUCKET_NAME = os.getenv("BUCKET_NAME")

if not ANTHROPIC_API_KEY or not STABILITY_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY and STABILITY_API_KEY are required.")
