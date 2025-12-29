from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AnalysisRequest(BaseModel):
    instagram_url: str

class PostResponse(BaseModel):
    instagram_id: str
    username: str
    caption: Optional[str] = None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    permalink: Optional[str]
    post_timestamp: Optional[datetime] = None
    ai_category: Optional[str] = "General"
    ai_summary: Optional[str] = None
    drink_category: Optional[str] = "Not Specified"

    class Config:
        from_attributes = True