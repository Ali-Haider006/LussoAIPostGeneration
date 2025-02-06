from PIL import Image, ImageDraw, ImageFont, ImageStat
import rembg
import extcolors
import io
import random
import math
import numpy as np

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
    elif position == "top-left":
        x = 10 
        y = 10
    elif position == "bottom-left":
        x = 10
        y = base_image.height - logo.height - 10
    elif position == "top-right":
        x = base_image.width - logo.width - 10
        y = 10
    else:
        x = base_image.width - logo.width - 10
        y = base_image.height - logo.height - 10

    base_image.paste(logo, (x, y), logo)

    output_buffer = io.BytesIO()
    base_image.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    return output_buffer.read()

# def get_contrasting_text_color(bg_color):
#     brightness = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2])
#     return (255, 255, 255) if brightness < 128 else (0, 0, 0)

def get_contrasting_text_color(bg_color):
    r, g, b = bg_color
    complementary_color = (255 - r, 255 - g, 255 - b)
    brightness = (0.299 * r + 0.587 * g + 0.114 * b)
    if brightness < 128:
        contrasting_color = tuple(min(c + 50, 255) for c in complementary_color)
    else:
        contrasting_color = tuple(max(c - 50, 0) for c in complementary_color)
    return contrasting_color

def wrap_text(draw, text, font, max_width):
    lines = []
    words = text.split()
    while words:
        line = words.pop(0)
        while words and draw.textlength(line + ' ' + words[0], font=font) <= max_width:
            line += ' ' + words.pop(0)
        lines.append(line)
    return '\n'.join(lines)

def add_text_overlay(image_path, text, bg_color, font_file, logo_bytes):
    image = Image.open(io.BytesIO(image_path)).convert("RGBA")
    width, height = image.size
    image_gray = image.convert('L')
    
    bg_width = int(width * 0.7)
    bg_height = int(height * 0.2)
    
    positions = [
        "top-left", "center-left", "bottom-left",
        "top-right", "center-right", "bottom-right"
    ]
    
    position_scores = []
    for position in positions:
        x = 0 if "left" in position else width - bg_width
        if position.startswith("top"):
            y = int(height * 0.15)
        elif position.startswith("center"):
            y = (height - bg_height) // 2
        else:
            y = int(height * 0.75)
        
        if x + bg_width > width or y + bg_height > height:
            continue
        
        roi = image_gray.crop((x, y, x + bg_width, y + bg_height))
        roi_array = np.array(roi)
        variance = np.var(roi_array)
        position_scores.append((position, variance))
    
    best_position = min(position_scores, key=lambda x: x[1])[0] if position_scores else "top-left"
    
    bg_color = extract_color_proportions(image)[0]["colorCode"]
    bg_color = bg_color.lstrip('#')
    bg_color = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))
    
    bg_x = 0 if "left" in best_position else width - bg_width
    if best_position.startswith("top"):
        bg_y = int(height * 0.15)
    elif best_position.startswith("center"):
        bg_y = (height - bg_height) // 2
    else:
        bg_y = int(height * 0.75)

    base_alpha = 180
    fade_start = int(bg_width * 0.8) if "left" in best_position else int(bg_width * 0.2)
    
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    for i in range(bg_width):
        if "left" in best_position:
            if i < fade_start:
                alpha = base_alpha - (i / fade_start) * 10
            else:
                alpha = base_alpha * (1 - ((i - fade_start) / (bg_width - fade_start)) ** 0.95)
        else:
            if i < fade_start:
                alpha = base_alpha * (i / fade_start)
            else:
                alpha = base_alpha * (1 - ((i - fade_start) / (bg_width - fade_start)) ** 0.95)
        
        for j in range(bg_height):
            vert_alpha = alpha * (0.95 + 0.05 * math.sin(j / bg_height * math.pi))
            draw.rectangle(
                [bg_x + i, bg_y + j, bg_x + i + 1, bg_y + j + 1],
                fill=(*bg_color, int(vert_alpha)),
            )
    
    font_size = 1
    font = ImageFont.truetype(font_file, font_size)
    max_width, max_height = int(bg_width * 0.95), int(bg_height * 0.8)
    
    while True:
        font = ImageFont.truetype(font_file, font_size)
        wrapped_text = wrap_text(draw, text, font, max_width)
        text_width, text_height = draw.textbbox((0, 0), wrapped_text, font=font)[2:]
        if text_width > max_width or text_height > max_height:
            break
        font_size += 1
    
    font_size -= 1
    font = ImageFont.truetype(font_file, font_size)
    wrapped_text = wrap_text(draw, text, font, max_width)
    
    text_x = bg_x + 25
    text_y = bg_y + (bg_height - draw.textbbox((0, 0), wrapped_text, font=font)[3]) // 2
    text_color = get_contrasting_text_color(bg_color)
    draw.text((text_x, text_y), wrapped_text, fill=text_color, font=font)
    
    combined = Image.alpha_composite(image, overlay)
    combined = combined.convert("RGB")
    
    output_buffer = io.BytesIO()
    combined.save(output_buffer, format="PNG")
    output_buffer.seek(0)
    
    logo_position_list = best_position.split("-")
    logo_position = ""

    if logo_position_list[0] == "top" or logo_position_list[0] == "center":
        logo_position = "bottom"
    else:
        logo_position = "top"

    if logo_position_list[1] == "left":
        logo_position += "-right"
    else:
        logo_position += "-left"
    
    print(logo_position)

    return overlay_logo(output_buffer.read(), logo_bytes, logo_position)

def generate_random_hex_color():
    dominant_channel = random.randint(200, 255)
    medium_channel = random.randint(100, 200)
    low_channel = random.randint(0, 100)
    
    channels = [dominant_channel, medium_channel, low_channel]
    random.shuffle(channels)
    
    hex_color = "#" + "".join(f"{value:02X}" for value in channels)
    return hex_color

# def add_text_overlay(image_path, text, bg_color, font_file):
#     position = random.choice(["top-left", "center-left", "bottom-left"])
#     image = Image.open(io.BytesIO(image_path)).convert("RGBA")
#     bg_color = extract_color_proportions(image)[0]["colorCode"]
#     bg_color = bg_color.lstrip('#')
#     bg_color = tuple(int(bg_color[i:i+2], 16) for i in (0, 2, 4))

#     width, height = image.size
    
#     bg_width = int(width * 0.7)
#     bg_height = int(height * 0.2)
#     bg_x = 0
#     if position == "top-left":
#         bg_y = int(height * 0.15)
#         base_alpha = 0 
#     elif position == "center-left":
#         bg_y = int(height * 0.5 - bg_height * 0.5)
#         base_alpha = 0 
#     else:
#         bg_y = int(height * 0.75)
#         base_alpha = 180 
    
#     overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
#     draw = ImageDraw.Draw(overlay)
    
#     fade_start = int(bg_width * 0.8) 
    
#     for i in range(bg_width):
#         if i < fade_start:
#             alpha = base_alpha - (i / fade_start) * 10
#         else:
#             alpha = base_alpha * (1 - ((i - fade_start) / (bg_width - fade_start)) ** 0.95)
            
#         for j in range(bg_height):
#             vert_alpha = alpha * (0.95 + 0.05 * math.sin(j / bg_height * math.pi))
#             draw.rectangle(
#                 [bg_x + i, bg_y + j, bg_x + i + 1, bg_y + j + 1],
#                 fill=(*bg_color, int(vert_alpha)),
#             )
    
#     font_size = 1
#     font = ImageFont.truetype(font_file, font_size)
#     max_width, max_height = int(bg_width * 0.95), int(bg_height * 0.8)
    
#     while True:
#         font = ImageFont.truetype(font_file, font_size)
#         wrapped_text = wrap_text(draw, text, font, max_width)
#         text_width, text_height = draw.textbbox((0, 0), wrapped_text, font=font)[2:]
#         if text_width > max_width or text_height > max_height:
#             break
#         font_size += 1
    
#     font_size -= 1
#     font = ImageFont.truetype(font_file, font_size)
#     wrapped_text = wrap_text(draw, text, font, max_width)
    
#     text_x = bg_x + 25
#     text_y = bg_y + (bg_height - draw.textbbox((0, 0), wrapped_text, font=font)[3]) // 2
#     text_color = get_contrasting_text_color(bg_color)
#     draw.text((text_x, text_y), wrapped_text, fill=text_color, font=font)
    
#     combined = Image.alpha_composite(image, overlay)
#     combined = combined.convert("RGB")
    
#     output_buffer = io.BytesIO()
#     combined.save(output_buffer, format="PNG")
#     output_buffer.seek(0)
#     return output_buffer.read()
