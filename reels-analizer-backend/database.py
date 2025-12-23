import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# .env içindeki DATABASE_URL'i al
# Örn: postgresql://postgres:sifre@localhost:5432/instagram_db
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Veritabanı motorunu oluştur
# PostgreSQL kullandığımız için ek parametreye (sqlite'daki gibi) gerek yok
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Veritabanı ile yapılacak her işlem için bir oturum (session) oluşturacak fabrika
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tüm veritabanı modellerimizin (tablolarımızın) miras alacağı temel sınıf
Base = declarative_base()

# FastAPI içinde veritabanı bağlantısını güvenli açıp kapatmak için yardımcı fonksiyon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()