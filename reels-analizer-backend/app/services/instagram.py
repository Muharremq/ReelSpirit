import httpx
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

async def fetch_instagram_page(target_username: str, after_cursor: str = None):
    """
    Instagram Graph API'den asenkron veri çeker.
    """
    url = f"https://graph.facebook.com/{settings.API_VERSION}/{settings.INSTAGRAM_BUSINESS_ID}"
    
    media_query = "media{caption,media_type,media_url,permalink,timestamp,id}"
    if after_cursor:
        media_query = f"media.after({after_cursor}){{caption,media_type,media_url,permalink,timestamp,id}}"

    params = {
        "fields": f"business_discovery.username({target_username}){{{media_query}}}",
        "access_token": settings.ACCESS_TOKEN
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            business_data = data.get('business_discovery', {})
            media_data = business_data.get('media', {})
            
            posts = media_data.get('data', [])
            next_cursor = media_data.get('paging', {}).get('cursors', {}).get('after')
            
            return posts, next_cursor
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Instagram API Hatası: {e.response.text}")
            return [], None
        except Exception as e:
            logger.error(f"Beklenmeyen Hata: {e}")
            return [], None