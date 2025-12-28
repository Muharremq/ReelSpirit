from sqlalchemy import Column, Integer, String, Text, DateTime, func
from database import Base

class InstagramPost(Base):
    __tablename__ = "instagram_posts"

    id = Column(Integer, primary_key=True, index=True)
    permalink = Column(Text)
    instagram_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(100), nullable=False, index=True)
    caption = Column(Text)
    media_type = Column(String(50))
    media_url = Column(Text)
    post_timestamp = Column(DateTime)
    
    # AI Analiz Sonuçları
    ai_category = Column(String(100), default="General")
    ai_summary = Column(Text)
    drink_category = Column(String(100), index=True, default="Not Specified")
    
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Post(id={self.instagram_id}, user={self.username})>"