import re

def extract_username(input_str: str) -> str:
    """
    Kullanıcının girdiği her türlü linkten kullanıcı adını çeker.
    Girdiler: 
    - https://www.instagram.com/kitsune.cim/
    - kitsune.cim
    - @kitsune.cim
    """
    # Önce @ işaretini temizle
    clean_str = input_str.replace("@", "").strip()
    
    # URL ise regex ile ayıkla
    match = re.search(r"instagram\.com/([a-zA-Z0-9._]+)", clean_str)
    if match:
        return match.group(1)
    
    # URL değilse (sadece username ise) temizlenmiş halini döndür
    return clean_str.split("/")[0]