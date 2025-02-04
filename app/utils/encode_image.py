import base64

def encode_image(image: str) -> str:
    return base64.b64encode(image).decode("utf-8")
    