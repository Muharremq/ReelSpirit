from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

# Proje içi importlar
import database
import models
import schemas
from utils import setup_logger

# Router Tanımlaması
# Not: Prefix kullanmıyoruz çünkü endpointler farklı (/posts ve /stats)
router = APIRouter(
    tags=["Posts & Stats"]
)

logger = setup_logger("Router-Posts")

@router.get("/posts/{username}", response_model=List[schemas.PostResponse])
def get_user_posts(username: str, db: Session = Depends(database.get_db)):
    """
    Kullanıcının veritabanındaki tüm analiz edilmiş postlarını getirir.
    """
    posts = db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(models.InstagramPost.post_timestamp.desc()).all()
    
    if not posts:
        # Boş liste dönebiliriz veya 404 verebiliriz, Frontend yapısına göre değişir.
        # Genelde boş liste dönmek daha güvenlidir.
        return []
        
    return posts

@router.get("/stats/{username}")
def get_drink_stats(username: str, db: Session = Depends(database.get_db)):
    """
    Angular frontend için gerekli istatistik verisini döner.
    Format: { total_posts: 50, categories: [{category: 'Viski', count: 10}, ...] }
    """
    # Kategori bazlı gruplama sorgusu
    stats_query = db.query(
        models.InstagramPost.drink_category,
        func.count(models.InstagramPost.id).label('count')
    ).filter(
        models.InstagramPost.username == username
    ).group_by(
        models.InstagramPost.drink_category
    ).all()
    
    if not stats_query:
        return {"username": username, "total_posts": 0, "categories": []}
    
    # Toplam post sayısını hesapla
    total_posts = sum(s.count for s in stats_query)
    
    # Frontend'in beklediği JSON formatına çevir
    categories_data = [
        {"drink_category": s.drink_category, "count": s.count} 
        for s in stats_query
    ]
    
    return {
        "username": username,
        "total_posts": total_posts,
        "categories": categories_data
    }