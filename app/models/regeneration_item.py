from pydantic import BaseModel, Field
from typing_extensions import Annotated, Optional

class RegenerationItem(BaseModel):
    post: str
    suggestion: Optional[str] = None
    model: Annotated[str, Field(min_length=3, max_length=50)] = "claude-3-5-haiku-20241022"
