from pydantic import BaseModel, Field, root_validator
from typing_extensions import Annotated

class RegenerationImage(BaseModel):
    purpose: str
    bzname: str
    preferredTone: str
    website: str
    hashtags: bool
    style: str
    model: Annotated[str, Field(min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"

