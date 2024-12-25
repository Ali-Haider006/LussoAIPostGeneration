from pydantic import BaseModel, Field, root_validator
from typing_extensions import Annotated

class Item(BaseModel):
    length: Annotated[int, Field(strict=True, ge=10, le=700)] = 150
    bzname: str
    purpose: str
    preferredTone: str
    website: str
    hashtags: bool
    color_theme: str
    model: Annotated[str, Field(min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"

    @root_validator(pre=True)
    def validate_purpose(cls, values):
        purpose = values.get("purpose")
        if purpose and len(purpose.split()) < 5:
            raise ValueError("Purpose must be at least 5 words long.")
        return values
