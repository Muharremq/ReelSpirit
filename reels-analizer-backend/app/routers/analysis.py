import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

# Proje içi importlar (Dosya yapınıza göre)
import database
import models
import schemas
from utils import extract_username, setup_logger
from services.instagram import fetch_instagram_page
from services.ai_analyzer import analyze_instagram_posts, merge_analysis_with_posts

# Router Tanımlaması
router = APIRouter(
    prefix="/analyze",
    tags=["Analysis"]  # Swagger UI'da başlık olarak görünür
)

logger = setup_logger("Router-Analysis")

# --- YARDIMCI FONKSİYONLAR (Local Helpers) ---

def save_posts_to_db(db: Session, final_data: list, username: str):
    """
    Analiz edilmiş verileri veritabanına kaydeder (Upsert mantığı).
    """
    saved_count = 0
    for item in final_data:
        insta_id = str(item.get('id', ''))
        
        # Mükerrer kayıt kontrolü
        exists = db.query(models.InstagramPost).filter(
            models.InstagramPost.instagram_id == insta_id
        ).first()
        
        if not exists:
            new_post = models.InstagramPost(
                instagram_id=insta_id,
                permalink=item.get('permalink'),
                username=username,
                caption=item.get('caption'),
                media_type=item.get('media_type'),
                media_url=item.get('media_url'),
                post_timestamp=item.get('timestamp'),
                # AI alanları
                ai_category=item.get('ai_category', 'Genel'),
                ai_summary=item.get('ai_summary', ''),
                drink_category=item.get('drink_category', 'Yok')
            )
            db.add(new_post)
            saved_count += 1
    
    if saved_count > 0:
        db.commit()
        logger.info(f"DB: {username} için {saved_count} yeni post kaydedildi.")
    return saved_count

async def process_remaining_posts_task(username: str, initial_cursor: str):
    """
    Arka planda (Background Task) çalışan asenkron fonksiyon.
    Kullanıcının profilindeki diğer sayfaları tarar.
    """
    logger.info(f"[BG-TASK] {username} için derinlemesine tarama başladı.")
    current_cursor = initial_cursor
    
    # Her background task kendi bağımsız DB oturumunu açmalıdır
    with database.SessionLocal() as db:
        try:
            while current_cursor:
                # 1. Instagram'dan Çek (Async)
                posts, next_cursor = await fetch_instagram_page(username, current_cursor)
                if not posts:
                    break
                
                # 2. AI Analizi Yap
                ai_results = analyze_instagram_posts(posts)
                final_data = merge_analysis_with_posts(posts, ai_results)
                
                # 3. DB'ye Kaydet
                save_posts_to_db(db, final_data, username)
                
                current_cursor = next_cursor
                
                # API Rate Limit koruması (2 saniye bekle)
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"[BG-TASK ERROR] {username} hatası: {e}")
        finally:
            logger.info(f"[BG-TASK] {username} taraması tamamlandı.")

# --- ENDPOINTLER ---

@router.post("/", response_model=List[schemas.PostResponse])
async def analyze_profile(
    request: schemas.AnalysisRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(database.get_db)
):
    """
    POST /analyze
    Kullanıcı analizini başlatır. İlk sayfayı döner, kalanı arkada işler.
    """
    username = extract_username(request.instagram_url)
    if not username:
        raise HTTPException(status_code=400, detail="Geçersiz Instagram URL'si")

    # 1. Cache Kontrolü: Eğer son analiz yeniyse (örnek: veri varsa) direkt dön
    # İsterseniz buraya 'updated_at' kontrolü ekleyebilirsiniz.
    existing_posts = db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(models.InstagramPost.post_timestamp.desc()).limit(50).all()

    if existing_posts:
        logger.info(f"{username} verileri DB'den getirildi.")
        return existing_posts

    # 2. Canlı Analiz (İlk Sayfa)
    logger.info(f"{username} için yeni analiz başlatılıyor...")
    raw_posts, next_cursor = await fetch_instagram_page(username)
    
    if not raw_posts:
        raise HTTPException(status_code=404, detail="Profil bulunamadı veya gönderisi yok.")

    # AI İşlemleri
    ai_results = analyze_instagram_posts(raw_posts)
    final_data = merge_analysis_with_posts(raw_posts, ai_results)
    
    save_posts_to_db(db, final_data, username)

    # 3. Geri Kalanları Arka Plana At
    if next_cursor:
        background_tasks.add_task(process_remaining_posts_task, username, next_cursor)
    
    # Yanıt Dön
    return db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(models.InstagramPost.post_timestamp.desc()).all()