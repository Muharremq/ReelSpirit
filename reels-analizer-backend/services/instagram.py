import requests
import os
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
API_VERSION = "v24.0" 

def fetch_instagram_data(target_username: str, max_posts: int = 100):
    """
    Tüm postları (veya belirlenen limite kadar) sayfalama kullanarak çeker.
    max_posts: Güvenlik için bir limit (AI maliyetini kontrol etmek için).
    """
    all_posts = []
    after_cursor = None
    has_next_page = True

    print(f"[FETCH] {target_username} profili için veri çekme işlemi başladı...")

    while has_next_page and len(all_posts) < max_posts:
        url = f"https://graph.facebook.com/{API_VERSION}/{INSTAGRAM_BUSINESS_ID}"
        
        # Sayfalama (pagination) parametresi: 
        # İlk istekte None'dır, sonraki isteklerde 'after(CURSOR_KODU)' eklenir.
        media_query = "media{caption,media_type,media_url,timestamp,id}"
        if after_cursor:
            media_query = f"media.after({after_cursor}){{caption,media_type,media_url,timestamp,id}}"

        params = {
            "fields": f"business_discovery.username({target_username}){{{media_query}}}",
            "access_token": ACCESS_TOKEN
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            business_data = data.get('business_discovery', {})
            media_data = business_data.get('media', {})
            
            # Gelen postları listeye ekle
            current_page_posts = media_data.get('data', [])
            all_posts.extend(current_page_posts)
            
            print(f"[FETCH] {len(all_posts)} post toplandı...")

            # Sonraki sayfa var mı kontrol et?
            paging = media_data.get('paging', {})
            after_cursor = paging.get('cursors', {}).get('after')
            
            if not after_cursor:
                has_next_page = False
                print("[FETCH] Tüm postlar çekildi.")
            
        except Exception as e:
            print(f"[ERROR] Veri çekme sırasında hata: {e}")
            break

    # Belirlenen limitin üzerini kes
    return all_posts[:max_posts]