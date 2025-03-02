from app.models.item import Item
from app.models.regeneration_item import RegenerationItem

def build_prompt_generation(item: Item, businessText: str) -> str:
    businessCategory = businessText["category"]
    businessDescription = businessText["description"]
    
    base_prompt = (
        f"Write a professional social media post, about {item.length} words long, "
        f"for the business {item.bzname}. "
        f"The post should achieve the goal: {item.purpose}. "
        f"Business Category: {businessCategory}. "
        f"Business Description: {businessDescription} " 
        f"Use a {item.preferredTone} tone. "
    )
    
    if item.website and item.website != "":
        base_prompt += f"Use the website {item.website} naturally. "
    
    if item.hashtags:
        return base_prompt + "Include relevant hashtags. Do not include any introductory or opening or ending or closing text."
    
    return base_prompt + "Do not include hashtags. Do not include any introductory or opening or ending or closing text."

def build_prompt_tagline(item: Item, post: str) -> str:
    base_prompt = (
        f"Create a social media image tagline for '{post}' that contains TWO DISTINCT PARTS separated by a line break: "
        f"1) A short, memorable slogan (5-6 words) using alliteration, rhyme, or wordplay\n"
        f"2) A 6-7 word descriptive text explaining {item.purpose} for {item.bzname}\n\n"
        f"Structure: [Catchy Phrase]\\n[Clear Description]\n"
        f"Example 1: 'Guardians at the Gate Standing Strong\\Reliable security for events businesses and properties'\n"
        f"Example 2: 'Power Up Protect Prevail Without Limits\\Cutting-edge IT solutions for security scalability and success'\n\n"
        f"Guidelines:\n"
        f"- Keep both parts completely separate\n"
        f"- First part: punchy and emotional\n"
        f"- Second part: practical and specific\n"
        f"- No punctuation in either part\n"
        f"- Avoid forced rhymes, keep natural\n"
        f"- Focus on clarity over cleverness\n"
        f"- Directly relate to: {item.purpose}\n"
        f"- Business name: {item.bzname}\n"
    )
    return base_prompt + "Do not include any introductory or opening or ending or closing text."

def build_prompt_tagline_no_purpose(item: Item, post: str) -> str:
    base_prompt = (
        f"Create a social media image tagline for '{post}' that contains TWO DISTINCT PARTS separated by a line break: "
        f"1) A short, memorable slogan (5-6 words) using alliteration, rhyme, or wordplay\n"
        f"2) A 6-7 word descriptive text explaining {item.purpose} for {item.bzname}\n\n"
        f"Structure: [Catchy Phrase]\\n[Clear Description]\n"
        f"Example 1: 'Fresh Finds Forever\\nQuality Goods Daily Drop'\n"
        f"Example 2: 'Style Unbound\\nTrendsetting Apparel Solutions'\n\n"
        f"Guidelines:\n"
        f"- Keep both parts completely separate\n"
        f"- First part: punchy and emotional\n"
        f"- Second part: practical and specific\n"
        f"- No punctuation in either part\n"
        f"- Avoid forced rhymes, keep natural\n"
        f"- Focus on clarity over cleverness\n"
        f"- Directly relate to: {item.purpose}\n"
    )
    return base_prompt + "Do not include any introductory or opening or ending or closing text, and keep the tagline very direct."

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

def build_dynamic_image_prompt(post_content: str, style: str, colors: str) -> str:
    return (
        f"Generate a prompt for a high-quality, visually appealing social media advertisement image. "
        f"Prompt engineer to perfection. Give the highest weight to the quality. "
        f"Incorporate these colors with emphasis and weighted importance: {colors}::2, ensuring they influence the mood and aesthetics. "
        f"Focus on the content theme: '{post_content}' to ensure the image aligns with the overall message. "
        f"Use the image style: {style} as the primary palette, ensuring the style dominates the design while remaining harmonious and professional. "
        "The image must be bold, bright, and well-lit, ensuring clear visibility. "
        "Specify the layout, composition, and visual elements to create a compelling advertisement image that effectively conveys the message. "
        "Prompt layout should specify the image prominently, followed by description, and then the theme or colors. "
        "Describe specific visual elements and composition, emphasizing balance, modern aesthetics, and alignment with the provided text. "
        "Use techniques like quality boosters, weighted terms, style modifiers, and other prompt engineering techniques to ensure optimal output. "
        "Please keep the generated prompt concise, clear, and as short as possible, with a maximum of 25 to 30 words. Avoid heavy details in the generated prompt. "
        "Do not include any introductory, opening, ending, or closing text; provide only the prompt needed for generating the advertisement image."
    )

def build_dynamic_image_prompt_purpose(post_content: str, style: str, purpose: str, colors: str) -> str:
    return (
        f"Generate a prompt for a high-quality, visually appealing social media advertisement image. "
        f"Prompt engineer to perfection. Give the highest weight to the quality and user suggestions: '{purpose}'. "
        f"Focus on the content theme: '{post_content}' to ensure the image aligns with the overall message. "
        f"Use the image style: {style} as the primary palette, ensuring the style dominates the design while remaining harmonious and professional. "
        f"Incorporate these colors with emphasis and weighted importance: {colors}::2, ensuring they influence the mood and aesthetics. "
        "The image must be bold, bright, and well-lit, ensuring clear visibility. "
        "Also use color names instead of hex code values. Specify the layout, composition, and visual elements to create a compelling advertisement image that effectively conveys the message. "
        "Prompt layout should specify the image prominently, followed by description, and then the theme or colors. "
        "Describe specific visual elements and composition, emphasizing balance, modern aesthetics, and alignment with the provided text and purpose. "
        "Use techniques like quality boosters, weighted terms, style modifiers, and other prompt engineering techniques. "
        "Please keep the generated prompt concise, clear, and as short as possible, with a maximum of 25 to 30 words. Avoid heavy details in the generated prompt. "
        "Do not include any introductory, opening, ending, or closing text; provide only the prompt needed for generating the advertisement image."
    )


def build_topics_gen_prompt_old(texts, no_of_topics):
    full_text = "Analyze the following content from the user's past posts:\n\n "
    n = 1
    for text in texts:
        full_text += f"Post {n}: '{text}', \n "
        n = n + 1
    full_text += f"Based on this analysis, generate {no_of_topics} unique and creative topics for future posts. Return the response as a JSON object in the following format:\n "
    full_text += "{\n'topics':[\n'Topics 1',\n 'Topics 2',\n 'Topics 3']}\n "
    full_text += "Ensure the topics are concise and relevant to the user's content style. "
    return full_text + "Do not include any introductory, opening, ending, or closing text; provide only the prompt needed for generating the advertisement image."


def build_topics_gen_prompt(texts, business_text, no_of_topics):
    available_posts = len(texts)
    businessCategory = business_text["category"]
    businessDescription = business_text["description"]
    full_text = (
        "You are a highly skilled creative content strategist. "
        "Your goal is to generate unique, engaging, and specific content topics "
        "that align with the style, tone, and themes of the provided social media posts "
        "and resonate with the business objectives outlined in the description.\n\n"
        "Business Category:\n"
        f"{businessCategory}\n\n"
        "Business Description:\n"
        f"{businessDescription}\n\n"
    )
    if not texts or len(texts) <= 0:
        full_text += "Analyze these previous social media posts for style, tone, topics, and themes:\n\n"
        for idx, text in enumerate(texts, 1):
            full_text += f"Post {idx}: {text.strip()}\n"
        
        full_text += f"\nBased on the above {available_posts} posts and the business description, "
        
        if available_posts < no_of_topics:
            full_text += (
                f"extrapolate and expand upon the identified themes and patterns. "
                f"Although only {available_posts} posts were provided, generate {no_of_topics} unique topics "
                f"by exploring related areas and maintaining consistency with the business objectives and style. "
            )
        else:
            full_text += f"generate {no_of_topics} unique topics "
    else:
        full_text += (
            f"by exploring related areas and maintaining consistency with the business objectives and style. "
            f"\nBased on the above the business description, generate {no_of_topics} unique topics "
        )

    full_text += (
        "that align with the business description and appeal to the target audience. "
        "Each topic should be a clear, specific content idea, not a generic theme.\n\n"
        "Format the response as a JSON object exactly as shown:\n"
        "{\n"
        "  'topics': [\n"
        "    'Specific Topic 1',\n"
        "    'Specific Topic 2',\n"
        "    'Specific Topic 3'\n"
        "  ]\n"
        "}\n\n"
        "Requirements:\n"
        "- Each topic should be 5-15 words\n"
        "- Topics should vary in focus while maintaining theme consistency\n"
        "- Avoid generic or repetitive suggestions\n"
        "- Match the writing style and tone of the original posts\n"
        "- Ensure relevance to the business description provided\n"
        "Do not include any introductory, opening, ending, or closing text. "
        "Return only the JSON object without any additional text."
    )
    
    return full_text

def build_prompt_bulk_generation(item: Item, businessText: str) -> str:
    businessCategory = businessText["category"]
    businessDescription = businessText["description"]
    base_prompt = (
        f"Write a professional social media post, about {item.length} words long, "
        f"for the business {item.bzname}. The topic of post is: {item.purpose}, "
        f"and using a {item.preferredTone} tone. "
        f"Business Category: {businessCategory}. "
        f"Business Description: {businessDescription} " 
    )
    
    if item.website and item.website != "":
        base_prompt += f"Use the website {item.website} naturally. "
    return base_prompt + "Include relevant hashtags. Do not include any introductory or opening or ending or closing text."

def build_prompt_font_selection(item: Item, tagline: str, font_list: list) -> str:
    base_prompt = (
        f"Select the most appropriate font from the following list for overlaying the tagline '{tagline}' on an image. "
        f"The font should align with the brand {item.bzname} and should align with image's style of: {item.style}. "
        f"Consider the tone of the tagline and the target audience while making the selection. "
        f"Here is the list of fonts:\n"
        f"{', '.join(font_list)}\n\n"
        f"Please provide the exact font name (including the file extension, e.g., 'AbrilFatface-Regular.ttf') "
        f"and nothing else. Do not add any commentary, punctuation, or formatting. "
        "Do not include any introductory or opening or ending or closing text."
    )
    return base_prompt
