from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import json

import models, schemas, utils, database
from services.instagram import fetch_instagram_data
from services.analyzer import analyze_instagram_posts, merge_analysis_with_posts

app = FastAPI(
    title="Reels Analizer API",
    description="Instagram içeriklerini AI ile analiz eden API",
    version="1.0.0"
)

# CORS ayarları (Angular'dan istek alabilmek için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=database.engine)

@app.post("/analyze", response_model=List[schemas.PostResponse])
def analyze_profile(request: schemas.AnalysisRequest, db: Session = Depends(database.get_db)):
    """Instagram profilini analiz eder ve veritabanına kaydeder"""
    
    print(f"\n{'='*60}")
    print(f"ANALİZ TALEBİ: {request.instagram_url}")
    print(f"{'='*60}\n")
    
    # 1. URL'den kullanıcı adını çıkar
    username = utils.extract_username(request.instagram_url)
    if not username:
        raise HTTPException(status_code=400, detail="Geçersiz Instagram URL'si")
    
    print(f"[1/6] Kullanıcı adı: {username}")
    
    # 2. Instagram'dan verileri çek
    raw_posts = fetch_instagram_data(username)
    
    if raw_posts is None:
        raise HTTPException(
            status_code=500, 
            detail="Instagram API bağlantı hatası. Token/ID'yi kontrol edin."
        )
    
    if not raw_posts:
        raise HTTPException(
            status_code=404, 
            detail="Profilde içerik bulunamadı veya profil kapalı/yok."
        )
    
    print(f"[2/6] Instagram'dan {len(raw_posts)} post çekildi")
    
    # DEBUG: İlk postun yapısını göster
    print(f"[DEBUG] Örnek post yapısı:")
    print(json.dumps(raw_posts[0], indent=2, ensure_ascii=False))
    
    # 3. AI ile analiz et
    print(f"[3/6] AI analizi başlatılıyor...")
    ai_results = analyze_instagram_posts(raw_posts)
    
    if not ai_results:
        print("[WARN] AI analizi boş döndü, fallback kullanılacak")
    
    print(f"[4/6] AI'dan {len(ai_results)} sonuç alındı")
    
    # 4. Sonuçları birleştir
    final_data = merge_analysis_with_posts(raw_posts, ai_results)
    
    # 5. Veritabanına kaydet (Duplicate kontrolü ile)
    print(f"[5/6] Veritabanına kaydediliyor...")
    saved_count = 0
    skipped_count = 0
    
    for item in final_data:
        # Instagram'dan gelen ID'yi al
        insta_id = str(item.get('id', ''))
        
        if not insta_id:
            print(f"[ERROR] Post ID bulunamadı, atlanıyor")
            continue
        
        # Daha önce kaydedilmiş mi kontrol et
        exists = db.query(models.InstagramPost).filter(
            models.InstagramPost.instagram_id == insta_id
        ).first()
        
        if exists:
            skipped_count += 1
            continue
        
        # Yeni kayıt oluştur
        new_post = models.InstagramPost(
            instagram_id=insta_id,
            username=username,
            caption=item.get('caption'),
            media_type=item.get('media_type'),
            media_url=item.get('media_url'),
            post_timestamp=item.get('timestamp'),
            ai_category=item.get('ai_category', 'Genel'),
            ai_summary=item.get('ai_summary', 'Özet yok'),
            drink_category=item.get('drink_category', 'Yok')
        )
        
        db.add(new_post)
        saved_count += 1
    
    try:
        db.commit()
        print(f"[6/6] ✓ {saved_count} yeni post kaydedildi, {skipped_count} zaten vardı")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Veritabanı hatası: {e}")
        raise HTTPException(status_code=500, detail=f"DB kayıt hatası: {str(e)}")
    
    # 6. Kullanıcının tüm postlarını döndür
    all_posts = db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(
        models.InstagramPost.post_timestamp.desc()
    ).all()
    
    print(f"\n{'='*60}")
    print(f"TOPLAM SONUÇ: {len(all_posts)} post")
    print(f"{'='*60}\n")
    
    return all_posts

@app.get("/")
def home():
    """API Sağlık Kontrolü"""
    return {
        "status": "online",
        "message": "Reels Analizer API Çalışıyor",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/posts/{username}")
def get_user_posts(username: str, db: Session = Depends(database.get_db)):
    """Belirli bir kullanıcının kayıtlı postlarını getirir"""
    posts = db.query(models.InstagramPost).filter(
        models.InstagramPost.username == username
    ).order_by(
        models.InstagramPost.post_timestamp.desc()
    ).all()
    
    if not posts:
        raise HTTPException(status_code=404, detail="Bu kullanıcıya ait post bulunamadı")
    
    return posts


@app.get("/stats/{username}")
def get_drink_stats(username: str, db: Session = Depends(database.get_db)):
    """Kullanıcının içerik kategorilerini istatistiksel olarak gösterir"""
    from sqlalchemy import func
    
    stats = db.query(
        models.InstagramPost.drink_category,
        func.count(models.InstagramPost.id).label('count')
    ).filter(
        models.InstagramPost.username == username
    ).group_by(
        models.InstagramPost.drink_category
    ).all()
    
    if not stats:
        raise HTTPException(status_code=404, detail="Bu kullanıcıya ait veri bulunamadı")
    
    return {
        "username": username,
        "total_posts": sum(s.count for s in stats),
        "categories": [
            {"drink_category": s.drink_category, "count": s.count} 
            for s in stats
        ]
    }