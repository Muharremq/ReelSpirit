from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# Kullanıcının frontend'den göndereceği veri yapısı
class AnalysisRequest(BaseModel):
    instagram_url: str

# Tek bir postun dışarıya sunulacak hali
class PostResponse(BaseModel):
    instagram_id: str
    username: str
    caption: Optional[str]
    media_type: str
    media_url: str
    post_timestamp: datetime
    ai_category: Optional[str]
    ai_summary: Optional[str]
    drink_category: Optional[str]

    class Config:
        from_attributes = True # SQLAlchemy modellerini otomatik dönüştürmek için