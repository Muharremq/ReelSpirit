import json
import re
from google import genai
from google.genai import types
from config import settings
from utils import setup_logger

logger = setup_logger(__name__)

# --- DÜZELTME 1: Prompt tamamen İngilizce mantığına uyarlandı ---
ANALYSIS_PROMPT = """
You are an expert Instagram content analyst. Your task is to analyze the given posts.
Respond in JSON format, strictly adhering to the rules below.

**TASKS:**
1. 'category': Content type (Gastronomy, Fashion, Sports, Nightlife, Travel, Art, etc.)
2. 'summary': Summary of the content in ENGLISH (max 10 words).
3. 'drink_category': If there is an alcoholic beverage, specify its type accurately.

**DRINK_CATEGORY RULES:**
- Single Spirit: "Whiskey", "Gin", "Rum", "Vodka", "Tequila", "Beer", "Wine", "Raki".
- Cocktails (Dominant Spirit): "Whiskey Cocktail", "Gin Cocktail", "Rum Cocktail", "Vodka Cocktail", "Tequila Cocktail".
- Cocktails (Mix/Ambiguous): "Mixed Cocktail".
- Coffee + Alcohol: "Coffee Cocktail".
- Liqueur based: "Liqueur Cocktail".
- No alcohol or unclear: "Other".

**IMPORTANT:** - Look for keywords in the text like 'cl', 'oz', 'recipe', 'mix'.
- Return ONLY a valid JSON list.
"""

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

def clean_caption(text):
    """Cleans up the caption text."""
    if not text or not isinstance(text, str):
        return ""
    # Remove hashtags and URLs
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'http\S+', '', text)
    # Remove excessive whitespace
    return " ".join(text.split())[:1000]

def analyze_instagram_posts(posts_data):
    """Analyzes posts using Gemini AI."""
    if not posts_data:
        return []

    logger.info(f"{len(posts_data)} posts are being prepared for analysis...")

    id_map = {}
    analysis_input = []
    
    for index, post in enumerate(posts_data):
        real_id = str(post.get("id") or post.get("instagram_id") or f"UNKNOWN_{index}")
        proxy_id = f"REF_{index}"
        id_map[proxy_id] = real_id
        
        cleaned_text = clean_caption(post.get("caption", ""))
        if not cleaned_text:
            cleaned_text = "No text, media only."
        
        analysis_input.append({
            "proxy_id": proxy_id,
            "text": cleaned_text
        })

    full_prompt = f"{ANALYSIS_PROMPT}\n\nDATA:\n{json.dumps(analysis_input, ensure_ascii=False)}"

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                temperature=0.3
            )
        )

        if not response.text:
            logger.warning("Gemini returned blank response. Switching to fallback.")
            return create_fallback_analysis(posts_data)

        ai_data = json.loads(response.text)
        
        # Handle dict vs list response formats
        ai_list = ai_data if isinstance(ai_data, list) else ai_data.get("results", [])

        final_results = []
        for res in ai_list:
            p_id = res.get("proxy_id")
            if p_id and p_id in id_map:
                final_results.append({
                    "id": id_map[p_id],
                    "category": res.get("category", "General"),
                    "summary": res.get("summary", "No summary available."),
                    "drink_category": res.get("drink_category", "Other")
                })
        
        logger.info(f"AI analysis completed: {len(final_results)} items processed.")
        return final_results

    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return create_fallback_analysis(posts_data)

def create_fallback_analysis(posts_data):
    """
    Fallback method: Regex-based analysis when AI fails.
    Updated with comprehensive English keywords.
    """
    logger.info("Running fallback analysis (Regex/Keyword based)...")
    results = []
    
    # --- DÜZELTME 2: Keyword listesi İngilizce varyasyonlarla zenginleştirildi ---
    keywords = {
        "Whiskey": ["viski", "whiskey", "whisky", "bourbon", "scotch", "jack daniels", "jameson"],
        "Gin": ["cin", "gin", "tanqueray", "gordon", "hendricks", "beefeater"],
        "Rum": ["rom", "rum", "bacardi", "havana club", "captain morgan"],
        "Vodka": ["votka", "vodka", "absolut", "smirnoff", "grey goose"],
        "Tequila": ["tekila", "tequila", "patron", "olmeca"],
        "Beer": ["bira", "beer", "lager", "ale", "ipa", "stout"],
        "Wine": ["şarap", "wine", "merlot", "cabernet", "chardonnay"],
        "Raki": ["rakı", "raki", "yeni rakı"],
        "Liqueur": ["likör", "liqueur", "baileys", "kahlua", "jagermeister", "cointreau"],
        "Coffee Cocktail": ["espresso martini", "irish coffee"]
    }

    cocktail_indicators = ["cocktail", "kokteyl", "mix", "recipe", "tarif", "cl", "oz"]

    for post in posts_data:
        caption = (post.get("caption") or "").lower()
        drink_cat = "Other"
        detected_drinks = []

        # 1. Hangi içkiler geçiyor?
        for cat, keys in keywords.items():
            if any(k in caption for k in keys):
                detected_drinks.append(cat)
        
        # 2. Mantıksal çıkarım
        is_cocktail = any(ind in caption for ind in cocktail_indicators)

        if "Coffee Cocktail" in detected_drinks:
            drink_cat = "Coffee Cocktail"
        elif len(detected_drinks) == 1:
            base = detected_drinks[0]
            if is_cocktail:
                drink_cat = f"{base} Cocktail"
            else:
                drink_cat = base
        elif len(detected_drinks) > 1:
             # Birden fazla alkol varsa, karışık kokteyl say
            if "Liqueur" in detected_drinks and len(detected_drinks) == 2:
                # Örn: Cin + Likör -> Cin baskın
                other = [d for d in detected_drinks if d != "Liqueur"][0]
                drink_cat = f"{other} Cocktail"
            else:
                drink_cat = "Mixed Cocktail"

        # Kategori belirleme (Basit)
        if drink_cat != "Other":
            category = "Gastronomy"
            summary = f"{drink_cat} recipe or showcase."
        elif any(x in caption for x in ["fashion", "style", "moda", "outfit"]):
            category = "Fashion"
            summary = "Fashion related content."
        else:
            category = "General"
            summary = "No summary available."

        results.append({
            "id": str(post.get("id") or post.get("instagram_id")),
            "category": category,
            "summary": summary,
            "drink_category": drink_cat
        })
    
    return results

def merge_analysis_with_posts(original_posts, ai_results):
    """Merges AI results with original post objects."""
    ai_map = {str(res['id']): res for res in ai_results}
    
    for post in original_posts:
        p_id = str(post.get('id') or post.get('instagram_id', ''))
        if p_id in ai_map:
            res = ai_map[p_id]
            post['ai_category'] = res.get('category', 'General')
            post['ai_summary'] = res.get('summary', '')
            post['drink_category'] = res.get('drink_category', 'Other')
        else:
            post['drink_category'] = 'Unprocessed'
            post['ai_category'] = 'General'
            post['ai_summary'] = ''
            
    return original_posts