def get_valid_overlay_position(position: str) -> str:
    valid_positions = {
        "top-left", "center-left", "bottom-left",
        "top-right", "center-right", "bottom-right"
    }
    
    response = position.strip()
    if response in valid_positions:
        return response
    else:
        return "bottom-right" 
