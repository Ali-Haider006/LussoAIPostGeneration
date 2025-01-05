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
        f"Write a professional tagline for the post {post}, maximum 3 to 4 words long, "
        f"and using a {item.preferredTone} tone. Do not include emojis and do not use punctuation. "
        "Also strictly do not generate words that have 2 consective same letters like beautifully has 'l' consecutively. "
        "Also strictly use simple words and short words, and avoid complex words. "
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

def build_dynamic_image_prompt_prev(post_content: str, tagline: str, color_theme: str) -> str:
    return (
        f"Generate a prompt for a high-quality, visually appealing social media advertisement image. "
        f"Prompt engineer to perfection to include the exact following text or words in the image: '{tagline.upper()}'. Do not specify fonts and other text related stuff. Use TEXT: '' to specify the text. "
        f"Focus on the content theme: '{post_content}' to ensure the image aligns with the overall message. "
        f"Use the color theme: {color_theme} as the primary palette, ensuring the colors dominate the design while remaining harmonious and professional. "
        "Also use colors names instead of hex code values. Specify the layout, composition, and visual elements to create a compelling advertisement image that effectively conveys the message. "
        f"First part of prompt should be text instruction followed by color theme and then rest, also put high empahize that text should be there in generated image. "
        "Prompt layout should be that first it should specify the text then, image or background on which text is overlayed and at end theme or colors. "
        "Describe specific visual elements and composition, emphasizing balance, modern aesthetics, and alignment with the provided text. "
        "While generating prompt keep in mind all the knowledge you have about prompt engineering and specially prompt engineering for image generation models. "
        "Use techniques like quality boosters, weighted terms, style modifiers and other prompt engineering techniques. "
        "Please keep the generated prompt concise, clear and as short as possible, maximum of 30 to 35 words also please avoid heavy details in genrated prompt. "
        "Do not include any introductory or opening or ending or closing text; provide only the prompt needed for generating the advertisement image."
    )

def build_dynamic_image_prompt(post_content: str, tagline: str, color_theme: str) -> str:
    return (
        f"Generate a prompt for a high-quality, visually appealing social media advertisement image. "
        f"Prompt engineer to perfection to include the exact following text or words in the image: '{tagline.upper()}'. Do not specify fonts and other text-related stuff. "
        "Use these exact same words 'TEXT OVERLAY: '', on background' to specify the text, and with background should also be there. Give the highest weight to the text. "
        f"Ensure the text '{tagline.upper()}' is prominently visible, central to the design, and integrated harmoniously with the background. "
        "Also ensure that text should be directly facing the viewer and make sure that text is treated as seperate entity from image. "
        f"Focus on the content theme: '{post_content}' to ensure the image aligns with the overall message. "
        f"Use the color theme: {color_theme} as the primary palette, ensuring the colors dominate the design while remaining harmonious and professional. "
        "The text must be bold, bright, and well-lit, ensuring clear visibility against the background. "
        "Also use colors names instead of hex code values. Specify the layout, composition, and visual elements to create a compelling advertisement image that effectively conveys the message. "
        "Prompt layout should specify the text prominently, followed by the image or background description, and then the theme or colors. "
        "Describe specific visual elements and composition, emphasizing balance, modern aesthetics, and alignment with the provided text. "
        "Use techniques like quality boosters, weighted terms, style modifiers, and other prompt engineering techniques. "
        "Please keep the generated prompt concise, clear, and as short as possible, with a maximum of 25 to 30 words. Avoid heavy details in the generated prompt. "
        "Do not include any introductory, opening, ending, or closing text; provide only the prompt needed for generating the advertisement image."
    )

def build_topics_gen_prompt(texts, no_of_topics):
    full_text = "Analyze the following content from the user's past posts:\n\n "
    n = 1
    for text in texts:
        full_text += f"Post {n}: '{text}', \n "
        n = n + 1
    full_text += f"Based on this analysis, generate {no_of_topics} unique and creative topics for future posts. Return the response as a JSON object in the following format:\n "
    full_text += "{\n'topics':[\n'Topics 1',\n 'Topics 2',\n 'Topics 3']}\n "
    full_text += "Ensure the topics are concise and relevant to the user's content style. "
    return full_text + "Do not include any introductory, opening, ending, or closing text; provide only the prompt needed for generating the advertisement image."

def build_prompt_bulk_generation(item: Item) -> str:
    return (
        f"Write a professional social media post, about {item.length} words long, "
        f"for the business {item.bzname}. The topic of post is: {item.purpose}, "
        f"and using a {item.preferredTone} tone. Use the website {item.website} naturally. "
        "Include relevant hashtags. Do not include any introductory or opening or ending or closing text."
    )
