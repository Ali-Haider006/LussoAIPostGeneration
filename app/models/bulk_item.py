from pydantic import BaseModel, Field, root_validator, validator
from typing_extensions import Annotated
from typing import Optional, Dict

class BulkItem(BaseModel):
    length: Annotated[int, Field(strict=True, ge=10, le=700)] = 150
    bzname: str
    purpose: str
    preferredTone: str
    website: str
    hashtags: bool
    style: str
    model: Annotated[str, Field(min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"

    @validator("style")
    def validate_style(cls, value):
        if not value or value.strip() == "":
            raise ValueError("Style parameter cannot be empty.")
        if len(value) > 300:
            raise ValueError("Custom style description cannot exceed 300 characters.")
        return value.strip() 

    @validator("bzname")
    def validate_bzname(cls, value):
        if not value or value.strip() == "":
            raise ValueError("Bzname parameter cannot be empty.")
        if len(value) > 100:
            raise ValueError("Bzname cannot exceed 100 characters.")
        return value.strip() 
    
    @validator("preferredTone")
    def validate_preferredTone(cls, value):
        if not value or value.strip() == "":
            raise ValueError("Preferred Tone parameter cannot be empty.")
        return value.strip()