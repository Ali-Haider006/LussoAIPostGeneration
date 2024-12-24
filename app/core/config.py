import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

if not ANTHROPIC_API_KEY or not STABILITY_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY and STABILITY_API_KEY are required.")
