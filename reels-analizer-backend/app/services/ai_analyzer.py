import json
import re
from google import genai
from google.genai import types
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

# Prompt metni kodun okunabilirliği için buraya alındı
ANALYSIS_PROMPT = """
Sen uzman bir Instagram içerik analistisin. Görevin verilen postları analiz etmek.
Aşağıdaki kurallara SIKI SIKIYA uyarak JSON formatında yanıt ver.

**GÖREVLER:**
1. 'category': İçerik türü (Gastronomi, Moda, Spor vb.)
2. 'summary': İçeriğin TÜRKÇE özeti (maks 10 kelime)
3. 'drink_category': Eğer alkollü içecek varsa türünü belirle.

**DRINK_CATEGORY KURALLARI:**
- Tek alkol varsa: "Viski", "Cin", "Bira", "Şarap", "Rakı" vb.
- Karışım varsa ve baskın bir ana alkol varsa: "Viski Kokteyli", "Cin Kokteyli".
- Eşit karışım veya belirsizse: "Karışık Kokteyl".
- Kahve bazlı alkollü ise: "Kahve Kokteyli".
- Alkol yoksa veya sadece görselse: "Yok".

**ÇIKTI FORMATI:**
Sadece ve sadece geçerli bir JSON listesi döndür.
"""

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

def clean_caption(text):
    """Caption temizliği yapar."""
    if not text or not isinstance(text, str):
        return ""
    # Hashtagleri ve URL'leri temizle
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'http\S+', '', text)
    return text.strip()[:1000] # Maksimum 1000 karakter al

def analyze_instagram_posts(posts_data):
    """Gemini ile postları analiz eder."""
    if not posts_data:
        return []

    logger.info(f"{len(posts_data)} adet post analize hazırlanıyor...")

    id_map = {}
    analysis_input = []
    
    for index, post in enumerate(posts_data):
        # Güvenilir bir ID oluştur
        real_id = str(post.get("id") or post.get("instagram_id") or f"UNKNOWN_{index}")
        proxy_id = f"REF_{index}"
        id_map[proxy_id] = real_id
        
        cleaned_text = clean_caption(post.get("caption", ""))
        if not cleaned_text:
            cleaned_text = "Metin yok, sadece görsel."
        
        analysis_input.append({
            "proxy_id": proxy_id,
            "text": cleaned_text
        })

    # Gemini'ye gönderilecek final mesaj
    full_prompt = f"{ANALYSIS_PROMPT}\n\nVERİLER:\n{json.dumps(analysis_input, ensure_ascii=False)}"

    try:
        # Gemini 2.0 Flash Exp modeli kullanımı
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                temperature=0.3
            )
        )

        if not response.text:
            logger.warning("Gemini boş yanıt döndürdü, fallback'e geçiliyor.")
            return create_fallback_analysis(posts_data)

        ai_data = json.loads(response.text)
        
        # Olası format farklılıklarını düzelt (dict vs list)
        ai_list = ai_data if isinstance(ai_data, list) else ai_data.get("results", [])

        final_results = []
        for res in ai_list:
            p_id = res.get("proxy_id")
            if p_id and p_id in id_map:
                final_results.append({
                    "id": id_map[p_id],
                    "category": res.get("category", "Genel"),
                    "summary": res.get("summary", "Özetlenemedi"),
                    "drink_category": res.get("drink_category", "Yok")
                })
        
        logger.info(f"AI Analizi tamamlandı: {len(final_results)} içerik işlendi.")
        return final_results

    except Exception as e:
        logger.error(f"Gemini API Hatası: {e}")
        return create_fallback_analysis(posts_data)

def create_fallback_analysis(posts_data):
    """AI çalışmazsa basit kural tabanlı analiz yapar."""
    logger.info("Fallback analiz çalıştırılıyor...")
    results = []
    
    keywords = {
        "Viski": ["viski", "whiskey", "bourbon"],
        "Cin": ["cin", "gin"],
        "Bira": ["bira", "beer"],
        "Şarap": ["şarap", "wine"],
        "Rakı": ["rakı"],
        "Kokteyl": ["kokteyl", "cocktail"]
    }

    for post in posts_data:
        caption = (post.get("caption") or "").lower()
        drink_cat = "Yok"
        
        for cat, keys in keywords.items():
            if any(k in caption for k in keys):
                drink_cat = cat if "kokteyl" not in caption else f"{cat} Kokteyli"
                break
        
        results.append({
            "id": str(post.get("id")),
            "category": "Genel",
            "summary": "Otomatik analiz (AI devre dışı)",
            "drink_category": drink_cat
        })
    return results

def merge_analysis_with_posts(original_posts, ai_results):
    """Orijinal veriyi AI sonuçlarıyla birleştirir."""
    ai_map = {res['id']: res for res in ai_results}
    
    for post in original_posts:
        p_id = str(post.get('id', ''))
        if p_id in ai_map:
            res = ai_map[p_id]
            post['ai_category'] = res.get('category')
            post['ai_summary'] = res.get('summary')
            post['drink_category'] = res.get('drink_category')
        else:
            post['drink_category'] = 'İşlenemedi'
    return original_posts