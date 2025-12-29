import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict

# Proje içi importlar
import database
import models
import schemas
from utils import extract_username, setup_logger
from services.instagram import fetch_instagram_page
from services.ai_analyzer import analyze_instagram_posts, merge_analysis_with_posts

# Router Tanımlaması
router = APIRouter(
    prefix="/analyze",
    tags=["Analysis"]
)

logger = setup_logger("Router-Analysis")

# --- GLOBAL DURUM TAKİBİ ---
# Hangi kullanıcının işlemi ne durumda? (processing, completed, error)
scan_status: Dict[str, str] = {}

# --- YARDIMCI FONKSİYONLAR ---

def save_posts_to_db(db: Session, final_data: list, username: str):
    """
    Analiz edilmiş verileri veritabanına kaydeder (Upsert logic).
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
                ai_category=item.get('ai_category', 'General'),
                ai_summary=item.get('ai_summary', ''),
                # Varsayılan değer 'Other' olarak güncellendi
                drink_category=item.get('drink_category', 'Other')
            )
            db.add(new_post)
            saved_count += 1
    
    if saved_count > 0:
        db.commit()
        logger.info(f"DB: {username} için {saved_count} yeni post kaydedildi.")
    return saved_count

async def process_remaining_posts_task(username: str, initial_cursor: str):
    """
    Arka planda çalışan asenkron görev.
    Diğer sayfaları tarar ve durumu günceller.
    """
    # 1. Durumu 'processing' yap
    scan_status[username] = "processing"
    logger.info(f"[BG-TASK] {username} için derinlemesine tarama başladı.")
    
    current_cursor = initial_cursor
    
    with database.SessionLocal() as db:
        try:
            while current_cursor:
                # Instagram'dan çek
                posts, next_cursor = await fetch_instagram_page(username, current_cursor)
                if not posts:
                    break
                
                # AI Analizi
                ai_results = analyze_instagram_posts(posts)
                final_data = merge_analysis_with_posts(posts, ai_results)
                
                # DB Kayıt
                save_posts_to_db(db, final_data, username)
                
                current_cursor = next_cursor
                
                # Rate limit koruması
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"[BG-TASK ERROR] {username} hatası: {e}")
            scan_status[username] = "error"
        finally:
            logger.info(f"[BG-TASK] {username} scan completed.")
            # 2. İşlem bitince durumu 'completed' yap
            scan_status[username] = "completed"

# --- ENDPOINTLER ---

@router.get("/status/{username}")
async def get_scan_status(username: str):
    """
    Frontend'in sürekli sorduğu (polling) durum endpointi.
    URL: /analyze/status/{username}
    """
    status = scan_status.get(username, "unknown")
    return {"status": status}

@router.post("/", response_model=List[schemas.PostResponse])
async def analyze_profile(
    request: schemas.AnalysisRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(database.get_db)
):
    """
    POST /analyze
    Kullanıcı analizini başlatır.
    """
    username = extract_username(request.instagram_url)
    if not username:
        raise HTTPException(status_code=400, detail="Invalid Instagram URL")

    # 1. DB Kontrolü (Cache)
    # Eğer işlem daha önce tamamlanmışsa ve veri varsa direkt dön
    existing_posts = db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(models.InstagramPost.post_timestamp.desc()).limit(50).all()

    # Eğer veri varsa ve şu an bir tarama işlemi yoksa cache'den dön
    # (Eğer tarama devam ediyorsa completed demiyoruz, kullanıcı beklesin istiyoruz)
    if existing_posts and scan_status.get(username) != "processing":
        logger.info(f"{username} verileri veritabanından getirildi.")
        # Durumu completed olarak işaretle ki frontend hemen durabilsin
        scan_status[username] = "completed" 
        return existing_posts

    # 2. Canlı Analiz Başlatılıyor
    logger.info(f"{username} için yeni analiz başlatılıyor...")
    
    # Durumu 'processing' olarak işaretle
    scan_status[username] = "processing"

    raw_posts, next_cursor = await fetch_instagram_page(username)
    
    if not raw_posts:
        # Hata durumunda statüyü temizle veya error yap
        scan_status[username] = "error"
        raise HTTPException(status_code=404, detail="Profile not found or no posts.")

    # İlk sayfa analizi
    ai_results = analyze_instagram_posts(raw_posts)
    final_data = merge_analysis_with_posts(raw_posts, ai_results)
    
    save_posts_to_db(db, final_data, username)

    # 3. Kalan Sayfalar İçin Arka Plan Görevi
    if next_cursor:
        background_tasks.add_task(process_remaining_posts_task, username, next_cursor)
    else:
        # Eğer başka sayfa yoksa işlem hemen bitmiştir
        scan_status[username] = "completed"
    
    # İlk 25 postu dön
    return db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(models.InstagramPost.post_timestamp.desc()).all()