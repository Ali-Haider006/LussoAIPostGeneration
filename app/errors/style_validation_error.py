from pydantic import BaseModel, validator

class StyleValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class StyleRequest(BaseModel):
    style: str

    @validator('style')
    def validate_style(cls, v):
        if not v or v.strip() == "":
            raise StyleValidationError("Style parameter cannot be empty")
            
        if len(v) > 300:
            raise StyleValidationError("Custom style description too long")
            
        return v.strip()