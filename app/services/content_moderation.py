from app.services.api_calls import fetch_response

async def is_content_explicit(content: str) -> bool:
    """
    Check for explicit content using AI moderation.

    Args:
        content (str): The content to analyze for explicit material.

    Returns:
        bool: True if explicit content is detected, False otherwise.
    """
    prompt = f"""Analyze this content for policy violations. Return 'true' if it contains:
    - Sexual content/nudity
    - Hate speech/discrimination
    - Violence/harm
    - Illegal activities
    - NSFW material
    - Harassment
    - Drug-related content

    Content: {content}

    Return ONLY 'true' or 'false' in lowercase:"""

    response = fetch_response(prompt, "claude-3-haiku-20240307")
    return response.content[0].text.strip().lower() == 'true'
