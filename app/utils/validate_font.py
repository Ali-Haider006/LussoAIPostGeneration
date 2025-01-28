def get_valid_font(font: str, font_list: list) -> str:
    response = font.strip()
    if response in font_list:
        return './fonts/' + response
    else:
        return './fonts/Roboto-Regular.ttf'
