# 1. Python sürümü
FROM python:3.9-slim

# 2. Çalışma dizini oluştur
WORKDIR /code

# 3. İşletim sistemi gereksinimleri
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 4. requirements.txt'yi kopyala (Artık ana dizinde olduğu için ./requirements.txt)
COPY requirements.txt .

# 5. Kütüphaneleri yükle
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Tüm backend klasörünü (app klasörü dahil) kopyala
COPY . .

# 7. ÇALIŞMA DİZİNİNİ DEĞİŞTİR (Kritik Nokta!)
# Senin kodların (main.py) "from routers import..." şeklinde yazıldığı için
# Python'un çalışma dizini 'app' klasörünün içi olmalı.
WORKDIR /code/app

# 8. Başlatma komutu
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]