#---------------------------------------------------------------------------------------
# intent_detector.py - Modul untuk mendeteksi intent/maksud dari pesan customer
#---------------------------------------------------------------------------------------

# modules/intent_detector.py

"""
Modul untuk mendeteksi intent/maksud dari pesan customer
Membantu persona memberikan respons yang sesuai dengan kebutuhan
"""

import re

# Kategori utama dari intent customer
INTENT_CATEGORIES = {
    "greeting": ["halo", "hai", "pagi", "siang", "malam", "selamat", "salam"],
    "inquiry_product": ["produk", "investasi", "saham", "reksa dana", "obligasi", "reksadana", "trading"],
    "inquiry_fee": ["biaya", "fee", "komisi", "charge", "harga"],
    "inquiry_registration": ["daftar", "register", "buka akun", "cara mulai", "buat akun"],
    "inquiry_process": ["cara", "proses", "langkah", "gimana"],
    "comparison": ["banding", "dibanding", "versus", "vs", "lebih baik"],
    "complaint": ["keluhan", "masalah", "error", "gagal", "tidak bisa", "gangguan"],
    "gratitude": ["terima kasih", "makasih", "thanks", "tq"],
    "farewell": ["sampai jumpa", "bye", "selamat tinggal"]
}

def detect_intent(message):
    """
    Mendeteksi intent dari pesan customer
    
    Args:
        message (str): Pesan dari customer
        
    Returns:
        dict: Intent yang terdeteksi dengan skor relevansi
    """
    message = message.lower()
    
    # Dictionary untuk menyimpan skor intent
    intent_scores = {category: 0 for category in INTENT_CATEGORIES}
    
    # Periksa setiap kategori intent
    for category, keywords in INTENT_CATEGORIES.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', message):
                intent_scores[category] += 1
    
    # Tambahkan intent lainnya yang mungkin terdeteksi
    if "?" in message:
        intent_scores["question"] = 1
    
    # Filter hanya intent dengan skor > 0
    detected_intents = {k: v for k, v in intent_scores.items() if v > 0}
    
    # Jika tidak ada intent yang terdeteksi, gunakan "general"
    if not detected_intents:
        detected_intents["general"] = 1
    
    return detected_intents