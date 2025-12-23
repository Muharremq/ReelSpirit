import requests
import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# Sabitleri .env'den çekiyoruz
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
# API Versiyonunu buraya yazabilirsin (Ekran görüntünde v24.0 görünüyor)
API_VERSION = "v24.0" 

def fetch_instagram_data(target_username: str):
    """
    Kullanıcı adını alır ve Instagram Graph API üzerinden 
    o profile ait postları (caption, url, id vb.) getirir.
    """
    
    # 1. API URL'sini oluşturuyoruz
    # Senin ekran görüntündeki yapının birebir aynısı:
    url = f"https://graph.facebook.com/{API_VERSION}/{INSTAGRAM_BUSINESS_ID}"
    
    # 2. Query parametrelerini (fields) tanımlıyoruz
    params = {
        "fields": f"business_discovery.username({target_username}){{media{{caption,media_type,media_url,timestamp,id}}}}",
        "access_token": ACCESS_TOKEN
    }
    
    try:
        # 3. İsteği gönderiyoruz
        response = requests.get(url, params=params)
        
        # 4. Hata kontrolü
        response.raise_for_status() # Eğer 400 veya 500 hatası varsa exception fırlatır
        
        data = response.json()
        
        # 5. JSON içindeki karmaşık yapıyı sadeleştiriyoruz
        # Graph API veriyi business_discovery -> media -> data hiyerarşisinde verir
        if "business_discovery" in data and "media" in data["business_discovery"]:
            posts = data["business_discovery"]["media"]["data"]
            return posts
        else:
            print("Hata: Veri yapısı beklendiği gibi değil veya profil bulunamadı.")
            return []

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Hatası Oluştu: {err}")
        # Hata detayını terminalde görebilmek için:
        print(f"Hata Mesajı: {response.text}")
        return None
    except Exception as e:
        print(f"Beklenmedik bir hata oluştu: {e}")
        return None

def clean_username(url_or_username: str):
    """
    Eğer kullanıcı tam link yapıştırırsa sadece kullanıcı adını ayıklar.
    Örn: https://www.instagram.com/kitsune.cim/ -> kitsune.cim
    """
    if "instagram.com/" in url_or_username:
        # Linkin sonundaki / işaretini temizle ve parçala
        username = url_or_username.rstrip("/").split("/")[-1]
        return username
    return url_or_username # Zaten kullanıcı adıysa direkt döndür