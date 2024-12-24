from PIL import Image
import rembg
import extcolors
import io

def remove_background(image_bytes: bytes) -> Image.Image:
    try:
        # Convert bytes to an image
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        # Use rembg to remove the background
        output_bytes = rembg.remove(image_bytes)
        # Convert the processed bytes back to an Image object
        output_image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
        return output_image
    except Exception as e:
        raise ValueError(f"Error in background removal: {e}")


def extract_color_proportions(image: Image.Image):
    try:
        colors, pixel_count = extcolors.extract_from_image(image, tolerance=33, limit=3)
        total_pixels = pixel_count
        color_percentages = [
            {
                "colorCode": "#" + "".join(f"{c:02x}" for c in color),
                "percent": round((count / total_pixels) * 100, 2)
            }
            for color, count in colors
        ]
        return color_percentages
    except Exception as e:
        raise ValueError(f"Error in color extraction: {e}")
    