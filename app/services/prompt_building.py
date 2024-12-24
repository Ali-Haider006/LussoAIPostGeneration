from app.models.item import Item
from app.models.regeneration_item import RegenerationItem

def build_prompt_generation(item: Item) -> str:
    base_prompt = (
        f"Write a professional social media post, about {item.length} words long, "
        f"for the business {item.bzname}. The post should achieve the goal: {item.purpose}, "
        f"and using a {item.preferredTone} tone. Use the website {item.website} naturally. "
    )
    if item.hashtags:
        return base_prompt + "Include relevant hashtags. Do not include any introductory or opening or ending or closing text."
    return base_prompt + "Do not include hashtags. Do not include any introductory or opening or ending or closing text."

def build_prompt_tagline(item: Item, post: str) -> str:
    base_prompt = (
        f"Write a professional tagline for the post {post}, maximum 6 words long, "
        f"and using a {item.preferredTone} tone. "
    )
    return base_prompt + "Do not include any introductory or opening or ending or closing text."

def build_prompt_regeneration(item: RegenerationItem) -> str:
    base_prompt = (
        f"Rewrite and improve the social media post, "
        f"Here is the previous post:{item.post}, "
    )

    if item.suggestion:
        base_prompt += f"Feedback or suggestion for improvement: {item.suggestion}. "
    else:
        base_prompt += "Improve the post generally by enhancing creativity, clarity, and engagement. "

    return base_prompt + "Regenerate the post based on this feedback while ensuring it adheres to the original instructions and aligns with the given purpose, and tone. Do not include any introductory or opening or ending or closing text just give me post text that can be directly posted."

def build_image_prompt(item: Item, tagline: str) -> str:
    refined_prompt = (
        f"Create a high-quality, professional social media advertisement poster for the following product: "
        f"Brand Name: '{item.bzname}' and Product Description: '{tagline}'. "
        f"The design should use the exact color palette: {item.color_theme}. "
        f"Strictly include only the following text in the image: '{item.bzname}' and '{tagline}'. "
        "No extra text, watermarks, or unrelated elements should appear in the image. "
        "Focus on a clean, minimalistic design with a professional, modern aesthetic. "
        "Use balanced typography, harmonious color integration, and a visually appealing layout to create a striking advertisement."
    )
    return refined_prompt

def build_static_image_prompt(post_content: str, tagline: str, bzname: str, color_theme: str) -> str:
    return (
        f"Professional {color_theme} advertisement: {post_content}. "
        f"Modern minimalist design with '{bzname}' in bold {color_theme} text, centered. "
        f"Below, '{tagline}' in clean typography. "
        "Elegant composition, balanced layout, 8K quality, commercial photography style. "
        "Sharp text, high contrast, professional lighting."
    )

def build_dynamic_image_prompt(post_content: str, tagline: str, color_theme: str) -> str:
    return (
        f"Generate a prompt for a high-quality, visually appealing social media advertisement image. "
        f"Ask to strictly include only the following text in the image the tagline: '{tagline}', and ask the model it should be visually distinct, engaging, and a central part of the design. "
        f"Tagline is must and should be in the image no matter what and prompt should put every emphasis on including tagline this tagline in image: '{tagline}' in generated image. "
        f"Focus on the content theme: '{post_content}' to ensure the image aligns with the overall message. "
        f"Use the color theme: {color_theme} as the primary palette, ensuring the colors dominate the design while remaining harmonious and professional. "
        "The design must prioritize the business name and tagline as key visual elements, integrating them seamlessly into the layout. "
        "Ask not to include extra text, watermarks, or unrelated elements in the image. "
        "Describe specific visual elements and composition, emphasizing balance, modern aesthetics, and alignment with the provided text. "
        "While generating prompt keep in mind all the knowledge you have about prompt engineering and specially prompt engineering for image generation models. "
        "Use techniques like quality boosters, weighted terms, style modifiers and other prompt engineering techniques. "
        "Do not include any introductory or opening or ending or closing text; provide only the prompt needed for generating the advertisement image."
    )
