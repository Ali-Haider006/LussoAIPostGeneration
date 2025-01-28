from app.services.api_calls import fetch_response

async def is_content_explicit(content: str) -> bool:
    """Check for explicit content using AI moderation"""
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

async def is_tagline_modern(tagline: str) -> bool:
    """Check if tagline meets modern marketing standards"""
    prompt = f"""Analyze this tagline for modernity:
    - Uses contemporary language
    - Follows current marketing trends
    - No outdated phrases
    - Appropriate for all audiences
    
    Tagline: {tagline}
    
    Return 'true' if modern and appropriate, 'false' otherwise. Use lowercase only:"""
    
    response = fetch_response(prompt, "claude-3-haiku-20240307")
    return response.content[0].text.strip().lower() == 'true'