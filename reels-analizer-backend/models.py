from sqlalchemy import Column, Integer, String, Text, DateTime, func
from database import Base

class InstagramPost(Base):
    __tablename__ = "instagram_posts"

    id = Column(Integer, primary_key=True, index=True)
    instagram_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(100), nullable=False, index=True)
    caption = Column(Text)
    media_type = Column(String(50))
    media_url = Column(Text)
    post_timestamp = Column(DateTime)
    
    ai_category = Column(String(100))
    ai_summary = Column(Text)
    
    drink_category = Column(String(100), index=True)  # <- INDEX EKLE
    
    created_at = Column(DateTime, server_default=func.now())