from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
import database

# Routerları import et
from routers import analysis, posts
from utils import setup_logger

logger = setup_logger("Main")

app = FastAPI(
    title="ReelSpirit API",
    version="2.1.0",
    description="Modular & Async Instagram Analyzer"
)

# CORS Ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"], # Frontend adresi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=database.engine)

# Router'ları sisteme dahil et
app.include_router(analysis.router)
app.include_router(posts.router)

@app.get("/")
def health_check():
    return {"status": "active", "system": "Reels Analyzer Modular API"}