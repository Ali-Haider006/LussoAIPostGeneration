import json
from app.core.logger import logger

def get_post_facebook(data, limit=None):
    """
    Recursively find all 'Text' fields in the Facebook dataset.
    
    Args:
        data: JSON string or dict containing Facebook post data
        limit: Optional maximum number of posts to return
        
    Returns:
        list: List of extracted text posts
        
    Raises:
        ValueError: If data is invalid or cannot be parsed
        TypeError: If input types are incorrect
    """
    try:
        # Handle both string and dict input
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON data: {str(e)}")
        elif isinstance(data, dict):
            parsed_data = data
        else:
            raise TypeError(f"Expected str or dict, got {type(data)}")

        texts = []

        def recursive_search(data):
            nonlocal texts

            # Stop if the limit is reached
            if limit is not None and len(texts) >= limit:
                return

            if isinstance(data, dict):
                for key, value in data.items():
                    if key.lower() == "text" and value:  # Check if value is not empty
                        texts.append(str(value).strip())  # Convert to string and strip whitespace
                        if limit is not None and len(texts) >= limit:
                            return
                    else:
                        recursive_search(value)

            elif isinstance(data, list):
                for item in data:
                    recursive_search(item)
                    if limit is not None and len(texts) >= limit:
                        return

        recursive_search(parsed_data)
        return texts

    except Exception as e:
        logger.error(f"Error extracting Facebook posts: {str(e)}")
        return []

def get_posts_linkedIn(data, limit=None):
    """
    Extract posts from LinkedIn data structure.
    
    Args:
        data: JSON string or dict containing LinkedIn post data
        limit: Optional maximum number of posts to return
        
    Returns:
        list: List of extracted post comments
        
    Raises:
        ValueError: If data is invalid or cannot be parsed
        KeyError: If required fields are missing
    """
    try:
        # Handle both string and dict input
        if isinstance(data, str):
            try:
                data_json = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON data: {str(e)}")
        elif isinstance(data, dict):
            data_json = data
        else:
            raise TypeError(f"Expected str or dict, got {type(data)}")

        # Safely navigate the nested structure
        payload = data_json.get("payload", {})
        list_of_posts = payload.get("listOfPosts", {})
        response = list_of_posts.get("response", {})
        posts_data = response.get("data", [])

        if not posts_data:
            logger.warning("No posts found in LinkedIn data")
            return []

        # Extract and clean posts
        posts = []
        for post in posts_data:
            if isinstance(post, dict) and "comment" in post:
                comment = str(post["comment"]).strip()
                if comment:  # Only add non-empty comments
                    posts.append(comment)
                    if limit is not None and len(posts) >= limit:
                        break

        return posts[:limit] if limit is not None else posts

    except Exception as e:
        logger.error(f"Error extracting LinkedIn posts: {str(e)}")
        return []

def get_text_business(data):
    return {
        "category": data["category"],
        "description": data["description"],
    }
