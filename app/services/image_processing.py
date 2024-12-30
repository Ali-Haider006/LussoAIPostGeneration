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
    
def overlay_logo(base_image_bytes, logo_bytes, position="bottom-right"):
    base_image = Image.open(io.BytesIO(base_image_bytes)).convert("RGBA")
    logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

    logo_width = base_image.width // 5
    logo = logo.resize(
        (logo_width, int(logo_width * logo.height / logo.width)),
        Image.Resampling.LANCZOS
    )

    if position == "center":
        x = (base_image.width - logo.width) // 2
        y = (base_image.height - logo.height) // 2
    elif position == "bottom-right":
        x = base_image.width - logo.width - 10
        y = base_image.height - logo.height - 10
    else:  
        x, y = 10, 10

    base_image.paste(logo, (x, y), logo)

    output_buffer = io.BytesIO()
    base_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    return output_buffer.read()
    