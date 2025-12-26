import requests
import os
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
API_VERSION = "v24.0" 

def fetch_instagram_page(target_username: str, after_cursor: str = None):
    """
    Instagram'dan tek seferde bir sayfa (25 post) veri çeker.
    after_cursor: Varsa bir sonraki sayfanın işaretçisidir.
    """
    url = f"https://graph.facebook.com/{API_VERSION}/{INSTAGRAM_BUSINESS_ID}"
    
    # Sayfalama varsa sorguya ekle
    media_query = "media{caption,media_type,media_url,permalink,timestamp,id}"
    if after_cursor:
        media_query = f"media.after({after_cursor}){{caption,media_type,media_url,permalink,timestamp,id}}"

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
        
        posts = media_data.get('data', [])
        next_cursor = media_data.get('paging', {}).get('cursors', {}).get('after')
        
        return posts, next_cursor
    except Exception as e:
        print(f"[INSTAGRAM-API-ERROR] {e}")
        return [], None