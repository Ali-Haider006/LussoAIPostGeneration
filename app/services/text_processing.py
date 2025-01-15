import json

def get_post_facebook(data, limit=None):
    """Recursively find all 'Text' fields in the dataset, with an optional limit on the number of results."""
    data = json.loads(data)
    texts = []

    def recursive_search(data):
        nonlocal texts

        # Stop if the limit is reached
        if limit is not None and len(texts) >= limit:
            return

        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() == "text":
                    texts.append(value)
                    if limit is not None and len(texts) >= limit:
                        return
                else:
                    recursive_search(value)

        elif isinstance(data, list):
            for item in data:
                recursive_search(item)
                if limit is not None and len(texts) >= limit:
                    return

    recursive_search(data)
    return texts

def get_posts_linkedIn(data, limit=None):
    data_json = json.loads(data)
    posts = data_json["payload"]["listOfPosts"]["response"]["data"]
    return [ sub['comment'] for sub in posts ][:limit]

def get_text_business(data):
    data_json = json.loads(data)
    return {
        "category": data_json["category"],
        "description": data_json["description"],
    }
