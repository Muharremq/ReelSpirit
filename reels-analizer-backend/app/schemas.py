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
    post_timestamp: Optional[datetime] = None
    ai_category: Optional[str] = "Genel"
    ai_summary: Optional[str] = None
    drink_category: Optional[str] = "Yok"

    class Config:
        from_attributes = True