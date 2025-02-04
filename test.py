from PIL import Image, ImageDraw, ImageFont
import numpy as np

# def calculate_brightness(image):
#     grayscale_image = image.convert("L")
#     pixels = np.array(grayscale_image)
#     brightness = np.mean(pixels)
#     return brightness

# def overlay_logo_and_text(base_image_path, logo_path, company_name, position, output_path, font_file="arial.ttf"):
#     base_image = Image.open(base_image_path).convert("RGBA")
#     logo = Image.open(logo_path).convert("RGBA")
    
#     logo_width = base_image.width // 5 
#     logo = logo.resize(
#         (logo_width, int(logo_width * logo.height / logo.width)),
#         Image.Resampling.LANCZOS
#     )
    
#     draw = ImageDraw.Draw(base_image)
    
#     # font file path like arial.ttf
#     try:
#         font = ImageFont.truetype(font_file, size=logo.height) # can divide logo.height by 2 to make it smaller
#     except IOError:
#         font = ImageFont.load_default()
    
#     text_bbox = draw.textbbox((0, 0), company_name, font=font)
#     text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    
#     MIN_FONT_SIZE = 32
#     print(f"Text width: {text_width}, Logo width: {logo.width}, Font size: {font.size} ...")
    
#     while text_width > logo.width and font.size > MIN_FONT_SIZE:
#         print(f"Text width: {text_width}, Logo width: {logo.width}, Font size: {font.size}")
#         font_size = font.size - 1 
#         font = ImageFont.truetype(font_file, size=font_size)
#         text_bbox = draw.textbbox((0, 0), company_name, font=font)
#         text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    
#     if text_width > logo.width:
#         text_width = logo.width  
    
#     if position == "center":
#         x_logo = (base_image.width - logo.width) // 2
#         y_logo = (base_image.height - logo.height - text_height) // 2
#     elif position == "bottom-right":
#         x_logo = base_image.width - logo.width - 10
#         y_logo = base_image.height - logo.height - text_height - 20
#     else:  
#         x_logo, y_logo = 10, 10
    
#     x_text = x_logo + (logo.width - text_width) // 2
#     y_text = y_logo + logo.height + 5 

#     background_sample = base_image.crop((x_logo, y_logo, x_logo + logo.width, y_logo + logo.height))
#     brightness = calculate_brightness(background_sample)

#     text_color = "black" if brightness > 128 else "white"
    
#     base_image.paste(logo, (x_logo, y_logo), logo)
    
#     draw.text((x_text, y_text), company_name, font=font, fill=text_color)
    
#     base_image.save(output_path, format="PNG")

# overlay_logo_and_text(
#     "./images/gen_post_1.jpeg", 
#     "./overlayed_images/logo.png", 
#     "Lusso Labs",
#     "bottom-right", 
#     "./overlayed_images/output.png"
# )

image = Image.open("./gen_post_5.jpeg").convert("RGBA")
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

print(position_scores)

best_position = min(position_scores, key=lambda x: x[1])[0] if position_scores else "top-left"

print(best_position)
