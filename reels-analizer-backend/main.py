from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import time

import models, schemas, utils, database
from services.instagram import fetch_instagram_page
from services.analyzer import analyze_instagram_posts, merge_analysis_with_posts

app = FastAPI(
    title="Reels Analizer API",
    description="Instagram içeriklerini AI ile analiz eden gelişmiş API",
    version="1.1.0"
)

# CORS Ayarları (Angular entegrasyonu için şart)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tabloları oluştur (Database'de yeni sütun eklediyseniz pgAdmin'den tabloyu düşürmeyi unutmayın)
models.Base.metadata.create_all(bind=database.engine)

# --- YARDIMCI FONKSİYONLAR ---

def save_posts_to_db(db: Session, final_data: list, username: str):
    """Postları veritabanına kaydeden ortak fonksiyon."""
    saved_count = 0
    for item in final_data:
        insta_id = str(item.get('id', ''))
        exists = db.query(models.InstagramPost).filter(models.InstagramPost.instagram_id == insta_id).first()
        
        if not exists:
            new_post = models.InstagramPost(
                instagram_id=insta_id,
                username=username,
                caption=item.get('caption'),
                media_type=item.get('media_type'),
                media_url=item.get('media_url'),
                post_timestamp=item.get('timestamp'),
                ai_category=item.get('ai_category', 'Genel'),
                ai_summary=item.get('ai_summary', 'Analiz edildi'),
                drink_category=item.get('drink_category', 'Yok')
            )
            db.add(new_post)
            saved_count += 1
    db.commit()
    return saved_count

def process_remaining_posts_task(username: str, initial_cursor: str):
    """Arka planda tüm profili tarayan fonksiyon."""
    db = database.SessionLocal() # Background task için manuel session
    current_cursor = initial_cursor
    
    print(f"\n[BG-TASK START] {username} için arka plan analizi başladı.")
    
    try:
        while current_cursor:
            # 1. Instagram'dan sıradaki 25'liyi çek
            posts, next_cursor = fetch_instagram_page(username, current_cursor)
            if not posts: break
            
            # 2. AI Analizi
            ai_results = analyze_instagram_posts(posts)
            final_data = merge_analysis_with_posts(posts, ai_results)
            
            # 3. DB'ye yaz
            save_posts_to_db(db, final_data, username)
            
            print(f"[BG-TASK] +{len(posts)} post analiz edildi. Sonraki cursor: {next_cursor}")
            current_cursor = next_cursor
            
            # Instagram Rate Limit koruması
            time.sleep(2) 
            
    except Exception as e:
        print(f"[BG-TASK-ERROR] {e}")
    finally:
        db.close()
        print(f"[BG-TASK FINISH] {username} taraması bitti.\n")

# --- ENDPOINTLER ---

@app.post("/analyze", response_model=List[schemas.PostResponse])
def analyze_profile(request: schemas.AnalysisRequest, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db)):
    """Profil analiz ana endpoint'i."""
    username = utils.extract_username(request.instagram_url)
    if not username:
        raise HTTPException(status_code=400, detail="Geçersiz URL.")

    # 1. DB Kontrolü (Varsa AI ile vakit kaybetme)
    existing_posts = db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(models.InstagramPost.post_timestamp.desc()).all()

    if existing_posts:
        print(f"[INFO] {username} verileri DB'den getirildi.")
        return existing_posts

    # 2. İLK SAYFA ANALİZİ (Kullanıcıya hızlı yanıt için)
    print(f"[NEW] {username} ilk kez analiz ediliyor...")
    raw_posts, next_cursor = fetch_instagram_page(username)
    
    if not raw_posts:
        raise HTTPException(status_code=404, detail="Profil içeriği boş veya ulaşılamaz.")

    ai_results = analyze_instagram_posts(raw_posts)
    final_data = merge_analysis_with_posts(raw_posts, ai_results)
    save_posts_to_db(db, final_data, username)

    # 3. KALANLARI ARKA PLANA AT
    if next_cursor:
        background_tasks.add_task(process_remaining_posts_task, username, next_cursor)
    
    # İlk 25'i hemen dön
    return db.query(models.InstagramPost).filter(models.InstagramPost.username == username).all()

@app.get("/posts/{username}")
def get_user_posts(username: str, db: Session = Depends(database.get_db)):
    """Kullanıcının tüm postlarını getirir (BG Task bittikçe burası dolar)."""
    return db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(models.InstagramPost.post_timestamp.desc()).all()

@app.get("/stats/{username}")
def get_drink_stats(username: str, db: Session = Depends(database.get_db)):
    """Angular'daki stats.total_posts ve stats.categories yapısına uygun döner"""
    from sqlalchemy import func
    
    stats_query = db.query(
        models.InstagramPost.drink_category,
        func.count(models.InstagramPost.id).label('count')
    ).filter(
        models.InstagramPost.username == username
    ).group_by(
        models.InstagramPost.drink_category
    ).all()
    
    if not stats_query:
        # Boş veri dönmek yerine Angular'ın hata almaması için default yapı dönelim
        return {"username": username, "total_posts": 0, "categories": []}
    
    return {
        "username": username,
        "total_posts": sum(s.count for s in stats_query),
        "categories": [
            {"drink_category": s.drink_category, "count": s.count} 
            for s in stats_query
        ]
    }

@app.get("/")
def health_check():
    return {"status": "ok", "service": "reels-analizer-api"}