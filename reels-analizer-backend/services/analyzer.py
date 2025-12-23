import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("GOOGLE_API_KEY bulunamadı! .env dosyasını kontrol edin.")

client = genai.Client(api_key=api_key)

def clean_caption(text):
    """Caption'dan hashtag ve linkleri temizler"""
    if text is None or not isinstance(text, str):
        return ""
    text = re.sub(r'#\w+', '', text)
    text = re.sub(r'http\S+', '', text)
    return text.strip()

def analyze_instagram_posts(posts_data):
    """
    Instagram postlarını Gemini AI ile analiz eder.
    """
    if not posts_data:
        print("[WARN] Hiç post verisi gelmedi")
        return []

    print(f"\n[DEBUG] İlk post örneği: {json.dumps(posts_data[0], indent=2, ensure_ascii=False)}")

    id_map = {}
    analysis_input = []
    
    for index, post in enumerate(posts_data):
        real_id = str(post.get("id") or post.get("instagram_id") or f"UNKNOWN_{index}")
        proxy_id = f"REF_{index}"
        id_map[proxy_id] = real_id
        
        raw_text = post.get("caption", "")
        cleaned_text = clean_caption(raw_text)
        
        if not cleaned_text:
            cleaned_text = "İçerik metni yok"
        
        analysis_input.append({
            "proxy_id": proxy_id,
            "text": cleaned_text[:500]
        })
        
        print(f"[DEBUG] Post {index}: ID={real_id}, Text uzunluğu={len(cleaned_text)}")

    print(f"\n[1/4] {len(analysis_input)} adet post Gemini'ye gönderiliyor...")

    prompt = f"""
Sen bir Instagram içerik analiz asistanısın. Özellikle alkollü içecek tariflerini kategorize etmekte uzmansın.

Aşağıdaki postları analiz et ve her biri için:
1. 'category': İçeriğin genel kategorisi (Gastronomi, Moda, vb.)
2. 'summary': İçeriğin TÜRKÇE özeti (maks 10 kelime)
3. 'drink_category': İçecek kategorisi - DETAYLI KURALLARA DİKKAT ET

**DRINK_CATEGORY KURALLARI:**

İçerikte alkollü içecek TARİFİ varsa, ana malzemeye göre kategorize et:

**TEK ALKOL İÇERENLER:**
- Sadece Viski/Whiskey: "Viski"
- Sadece Rom/Rum: "Rom"
- Sadece Cin/Gin: "Cin"
- Sadece Votka/Vodka: "Votka"
- Sadece Tekila/Tequila: "Tekila"
- Sadece Likör: "Likör"
- Sadece Şarap: "Şarap"
- Sadece Bira: "Bira"
- Sadece Rakı: "Rakı"

**KOKTEYL (Karışık İçecekler) - ANA ALKOLE GÖRE:**
Eğer tarif birden fazla alkol içeriyorsa veya kokteyl ismi geçiyorsa, EN BASKIN/ANA alkolü belirle:
- Viski + başka alkol/likör: "Viski Kokteyli"
- Rom + başka alkol/likör: "Rom Kokteyli"
- Cin + başka alkol/likör: "Cin Kokteyli"
- Votka + başka alkol/likör: "Votka Kokteyli"
- Tekila + başka alkol/likör: "Tekila Kokteyli"
- Likör + başka likör (base alkol yok): "Likör Kokteyli"
- Birden fazla farklı base alkol (viski+rom gibi): "Karışık Kokteyl"

**DİĞER:**
- Kahve bazlı (Irish Coffee, Espresso Martini vb.): "Kahve Kokteyli"
- İçecek tarifi değilse veya alkolsüz: "Yok"

**ÖNEMLİ NOTLAR:**
- Caption'daki malzeme listesini DİKKATLE oku ve MİKTARLARA dikkat et
- En çok kullanılan/ön plana çıkan alkol hangisi ise o ana alkoldür
- Örnek: "6cl viski + 1cl likör" → "Viski Kokteyli" (viski baskın)
- Örnek: "3cl rom + 3cl viski" → "Karışık Kokteyl" (eşit oran)
- Sadece görsel varsa ama tarif yoksa: "Yok"
- 'proxy_id' değerlerini AYNEN koru
- SADECE geçerli JSON formatında yanıt ver

POSTLAR:
{json.dumps(analysis_input, ensure_ascii=False, indent=2)}

BEKLENEN FORMAT:
[
  {{"proxy_id": "REF_0", "category": "Gastronomi", "summary": "Bal ve tarçınlı viski kokteyoli", "drink_category": "Viski Kokteyli"}},
  {{"proxy_id": "REF_1", "category": "Gastronomi", "summary": "Sade viski tarifi", "drink_category": "Viski"}},
  {{"proxy_id": "REF_2", "category": "Gastronomi", "summary": "Rom ve likör karışımı", "drink_category": "Rom Kokteyli"}}
]
"""

    try:
        print("[2/4] Gemini API'ye istek gönderiliyor...")
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                temperature=0.3,
                top_p=0.8,
                top_k=40
            )
        )

        if not response or not response.text:
            print("[ERROR] Gemini boş yanıt döndürdü (Safety filter olabilir)")
            return create_fallback_analysis(posts_data)

        print(f"[3/4] Yanıt alındı ({len(response.text)} karakter)")
        
        ai_data = json.loads(response.text)
        
        if isinstance(ai_data, list):
            ai_list = ai_data
        elif isinstance(ai_data, dict):
            ai_list = ai_data.get("results") or ai_data.get("analyses") or ai_data.get("posts") or []
        else:
            print("[ERROR] Beklenmeyen yanıt formatı")
            return create_fallback_analysis(posts_data)
        
        # --- DÜZELTİLEN KISIM: Bu blok try içinde olmalıydı ---
        final_results = []
        for res in ai_list:
            p_id = res.get("proxy_id") or res.get("id")
            if p_id and p_id in id_map:
                final_results.append({
                    "id": id_map[p_id],
                    "category": res.get("category", "Genel"),
                    "summary": res.get("summary", "Analiz tamamlandı"),
                    "drink_category": res.get("drink_category", "Yok")
                })
        return final_results
        # ---------------------------------------------------

    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parse hatası: {e}")
        return create_fallback_analysis(posts_data)
    except Exception as e:
        print(f"[ERROR] Gemini hatası: {type(e).__name__} - {str(e)}")
        return create_fallback_analysis(posts_data)

def create_fallback_analysis(posts_data):
    """AI başarısız olursa regex-based analiz yapar"""
    print("[INFO] Fallback analiz devreye girdi")
    results = []
    
    # Alkol türleri için keyword mapping
    drink_keywords = {
        "viski": ["viski", "whiskey", "whisky", "bourbon"],
        "rom": ["rom", "rum"],
        "cin": ["cin", "gin"],
        "votka": ["votka", "vodka"],
        "tekila": ["tekila", "tequila"],
        "likör": ["likör", "liqueur", "baileys", "amaretto", "kahlua"],
        "şarap": ["şarap", "wine", "kırmızı şarap", "beyaz şarap"],
        "bira": ["bira", "beer"],
        "rakı": ["rakı", "raki"],
        "kahve": ["espresso", "kahve", "coffee"]
    }
    
    # Kokteyl belirten kelimeler
    cocktail_indicators = ["kokteyl", "cocktail", "karışık", "mix"]
    
    for post in posts_data:
        post_id = str(post.get("id") or post.get("instagram_id") or "unknown")
        caption = (post.get("caption") or "").lower()
        
        # Alkol türlerini tespit et
        detected_drinks = []
        for drink_type, keywords in drink_keywords.items():
            if any(kw in caption for kw in keywords):
                detected_drinks.append(drink_type)
        
        # Drink category belirleme
        drink_category = "Yok"
        
        if len(detected_drinks) == 0:
            drink_category = "Yok"
        
        elif len(detected_drinks) == 1:
            # Tek alkol var
            base = detected_drinks[0].capitalize()
            
            # Kokteyl indicator'ı var mı kontrol et
            is_cocktail = any(ind in caption for ind in cocktail_indicators)
            
            # Kahve özel durumu
            if base == "Kahve":
                drink_category = "Kahve Kokteyli"
            elif is_cocktail or "cl" in caption or "ölçü" in caption:
                # Tarif formatında ise kokteyl kategorisi ver
                drink_category = f"{base} Kokteyli"
            else:
                drink_category = base
        
        else:
            # Birden fazla alkol var
            # Kahve varsa öncelik ver
            if "kahve" in detected_drinks:
                drink_category = "Kahve Kokteyli"
            # Likör hariç gerçek base alkol sayısını kontrol et
            elif "likör" in detected_drinks:
                base_alcohols = [d for d in detected_drinks if d != "likör"]
                if len(base_alcohols) == 1:
                    drink_category = f"{base_alcohols[0].capitalize()} Kokteyli"
                else:
                    drink_category = "Karışık Kokteyl"
            else:
                # İlk tespit edilen ana alkol
                drink_category = f"{detected_drinks[0].capitalize()} Kokteyli"
        
        # Kategori ve özet
        if drink_category != "Yok":
            category = "Gastronomi"
            summary = f"{drink_category} tarifi"
        elif any(word in caption for word in ["tarif", "içecek"]):
            category = "Gastronomi"
            summary = "İçecek tarifi"
        elif any(word in caption for word in ["moda", "stil", "outfit"]):
            category = "Moda"
            summary = "Moda ve stil içeriği"
        else:
            category = "Genel"
            summary = "Çeşitli içerik"
        
        results.append({
            "id": post_id,
            "category": category,
            "summary": summary,
            "drink_category": drink_category
        })
    
    return results

def merge_analysis_with_posts(original_posts, ai_results):
    ai_map = {str(res['id']): res for res in ai_results}
    
    for post in original_posts:
        post_id = str(post.get('id') or post.get('instagram_id', ''))
        if post_id in ai_map:
            post['ai_category'] = ai_map[post_id].get('category', 'Genel')
            post['ai_summary'] = ai_map[post_id].get('summary', 'Analiz yapıldı')
            post['drink_category'] = ai_map[post_id].get('drink_category', 'Yok')
        else:
            post['drink_category'] = "Bilinmiyor"
    return original_posts