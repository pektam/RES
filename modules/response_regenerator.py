# modules/response_regenerator.py

"""
Modul untuk meregenerasi respons AI menjadi lebih natural
Diterapkan sebagai lapisan tambahan tanpa mengubah modul inti
"""

import re
import random

# Fungsi di luar class
def get_custom_templates():
    """
    Template kustom untuk respons umum
    """
    return {
        # Untuk pertanyaan modal awal
        "modal_awal": [
            "399rb bang, itu minimal nya",
            "Minimal 399 ribu aja bang, langsung bisa cuan",
            "Cuma 399rb bang, mau join?",
            "Modal awal 399rb bang, kecil tapi lumayan hasilnya",
            "399rb aja bg, gak mahal kok"
        ],
        
        # Untuk pertanyaan pencairan
        "pencairan": [
            "Biasanya 1-2 hari kerja bang, sabar ya",
            "Pencairan nya kirim WA ke admin aja ya bg, ntar dibantu",
            "Bisa langsung WA admin buat pencairan, cepet kok",
            "Pencairan biasanya lancar bg, asal datanya bener semua",
            "Cair kok bg, tenang aja"
        ],
        
        # Untuk greeting
        "greeting": [
            "Iya bang, kenapa?",
            "Yo, ada apa bg?",
            "Siap bg, mau tanya apa?",
            "Yo bro, lagi butuh apa nih?",
            "Oke gan, ada yang mau ditanyain?"
        ],
        
        # Untuk pertanyaan keuntungan
        "keuntungan": [
            "Lumayan bang, gw dapet 5% per bulan",
            "Tergantung paket nya bg, tapi minimal 5% per bulan",
            "Kalo normal sih 5-10% bulanan bang",
            "5-10% per bulan bg, lumayan buat tambahan",
            "Gw sih dapet 5-10% per bulan, tapi tergantung juga sih"
        ]
    }

# Fungsi di luar class
def match_template(message, username=""):
    """
    Cocokkan pesan dengan template yang sesuai
    
    Args:
        message (str): Pesan dari user
        username (str): Username dari profil
        
    Returns:
        str: Template respons atau None jika tidak cocok
    """
    message = message.lower()
    templates = get_custom_templates()
    
    # Cek pertanyaan modal awal
    if any(keyword in message for keyword in ["modal", "deposit", "setor", "biaya awal"]):
        return random.choice(templates["modal_awal"])
    
    # Cek pertanyaan pencairan
    elif any(keyword in message for keyword in ["cair", "tarik", "wd", "withdraw", "ambil dana"]):
        return random.choice(templates["pencairan"])
    
    # Cek greeting simpel
    elif len(message.split()) <= 2 and any(greeting in message for greeting in ["p", "hai", "halo", "bang", "bro", "gan", "om", "bg"]):
        return random.choice(templates["greeting"])
    
    # Cek pertanyaan keuntungan
    elif any(keyword in message for keyword in ["untung", "profit", "hasil", "return", "dapat", "dapet", "cuan"]):
        return random.choice(templates["keuntungan"])
    
    # Default: tidak ada yang cocok
    return None

class ResponseRegenerator:
    """
    Kelas untuk mengubah respons formal AI menjadi percakapan natural
    """
    
    def __init__(self):
        # Sapaan kasual
        self.sapaan = ["bang", "bro", "bg", "om", "gan", "kk", "brader"]
        
        # Kata sambung kasual
        self.kata_sambung = ["eh", "btw", "oh iya", "nah", "jadi gini", "gini lho", "jujur aja", "sebenernya"]
        
        # Kata penutup kasual
        self.penutup = ["sih", "sih ya", "gitu", "gitu deh", "gitu aja", "ya", "nih", "cuy", "gan"]
        
        # Emoji kasual (gunakan seperlunya)
        self.emoji = ["👍", "😁", "🙏", "💯", "🔥", "👌", "💪"]
        
        # Filler words
        self.filler = ["hmm", "umm", "hehe", "wkwk", "lho", "dong", "kan", "kok", "lah", "deh"]
    
    def regenerate(self, original_response, input_message, username=None):
        """
        Regenerasi respons AI menjadi lebih natural
        
        Args:
            original_response (str): Respons asli dari AI
            input_message (str): Pesan dari user
            username (str, optional): Username dari profil
            
        Returns:
            str: Respons yang sudah diregenerasi
        """
        # Cek apakah ada template kustom yang cocok
        template_match = match_template(input_message, username)
        if template_match:
            return template_match
        
        # Jika tidak ada template yang cocok, lanjutkan dengan regenerasi biasa
        kasual_level = self._detect_casual_level(input_message)
        persona = self._get_persona(username) if username else "neutral"
        
        if kasual_level < 0.3:
            return self._make_semi_casual(original_response)
        elif kasual_level > 0.7:
            return self._make_very_casual(original_response, persona)
        else:
            return self._make_casual(original_response, persona)
    
    def _detect_casual_level(self, message):
        """
        Deteksi tingkat kekasual-an pesan
        
        Args:
            message (str): Pesan dari user
            
        Returns:
            float: Skor 0-1, makin tinggi makin kasual
        """
        message = message.lower()
        
        # Kata-kata yang menandakan kasual
        casual_markers = [
            "gw", "gue", "elu", "lu", "lo", "bro", "gan", "gaes", "guys", 
            "banget", "bgt", "sih", "dong", "kali", "kek", "cuy", "bruh",
            "wkwk", "haha", "anjir", "mantap", "mantul", "gass", "gas"
        ]
        
        # Kata-kata yang menandakan formal
        formal_markers = [
            "saya", "anda", "mohon", "terima kasih", "maaf", "selamat", 
            "hormat", "kepada", "bapak", "ibu", "saudara", "kiranya"
        ]
        
        # Hitung skor
        casual_count = sum(1 for word in casual_markers if word in message)
        formal_count = sum(1 for word in formal_markers if word in message)
        
        # Tambahkan skor untuk emoji, singkatan, dan penulisan tidak baku
        if re.search(r'[😀-🙏]', message):  # Emoji
            casual_count += 2
            
        if re.search(r'\b[A-Za-z]{1,2}\b', message):  # Singkatan pendek
            casual_count += 1
            
        # Faktor panjang pesan (pesan pendek cenderung kasual)
        if len(message.split()) <= 5:
            casual_count += 1
        
        # Hitung skor final
        total = casual_count + formal_count
        if total == 0:
            return 0.5  # Default mid-level
        
        return casual_count / total
    
    def _get_persona(self, username):
        """
        Dapatkan persona berdasarkan username
        
        Args:
            username (str): Username profil
            
        Returns:
            str: Tipe persona
        """
        # Mapping persona berdasarkan username
        persona_map = {
            "fahrul": "percaya_diri",
            "agus": "analitis",
            "dharma": "strategis",
            "darlina": "supportif",
            "mikayla": "inovatif"
        }
        
        # Default ke neutral jika tidak ada dalam map
        return persona_map.get(username.lower(), "neutral")
    
    def _make_semi_casual(self, text):
        """
        Buat respons semi kasual (sedikit formal)
        
        Args:
            text (str): Respons asli
            
        Returns:
            str: Respons semi kasual
        """
        # Pecah menjadi kalimat
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Ambil maksimal 2 kalimat pertama
        sentences = sentences[:2]
        
        # Gabungkan kembali
        shortened = ' '.join(sentences)
        
        # Ganti beberapa kata formal dengan semi formal
        replacements = {
            r'\bSilakan\b': 'Silahkan',
            r'\bMohon\b': 'Tolong',
            r'\bterima kasih\b': 'makasih',
            r'\bdemikian\b': 'gitu aja',
            r'\bInformasi\b': 'Info',
            r'\bmengenai\b': 'tentang',
            r'\bsangat\b': 'banget'
        }
        
        for pattern, replacement in replacements.items():
            shortened = re.sub(pattern, replacement, shortened, flags=re.IGNORECASE)
        
        return shortened
    
    def _make_casual(self, text, persona):
        """
        Buat respons kasual
        
        Args:
            text (str): Respons asli
            persona (str): Tipe persona
            
        Returns:
            str: Respons kasual
        """
        # Ekstrak info penting dari respons asli
        keywords = self._extract_key_info(text)
        
        # Pilih sapaan random
        sapaan = random.choice(self.sapaan)
        
        # Buat template kasual berdasarkan keyword
        templates = [
            f"Yoi {sapaan}, {keywords[0]} sih kalau mau tau.",
            f"Gini {sapaan}, {keywords[0]} aja ya.",
            f"{keywords[0]} aja {sapaan}, simpel kan?",
            f"Oh, {keywords[0]} gitu lho {sapaan}.",
            f"Kalau itu sih {keywords[0]} {sapaan}."
        ]
        
        # Pilih template random
        response = random.choice(templates)
        
        # Tambahkan emoji 30% dari waktu
        if random.random() < 0.3:
            response += f" {random.choice(self.emoji)}"
        
        return response
    
    def _make_very_casual(self, text, persona):
        """
        Buat respons sangat kasual
        
        Args:
            text (str): Respons asli
            persona (str): Tipe persona
            
        Returns:
            str: Respons sangat kasual
        """
        # Ekstrak info penting
        keywords = self._extract_key_info(text)
        
        # Pilih sapaan random
        sapaan = random.choice(self.sapaan)
        filler = random.choice(self.filler)
        
        # Gabungkan semua elemen
        casual_response = f"{random.choice(['wkwk', 'haha', 'yepp', 'siapp'])} {sapaan}, {keywords[0]} {filler}. {keywords[1] if len(keywords) > 1 else ''}"
        
        # Tambahkan emoji 50% dari waktu
        if random.random() < 0.5:
            casual_response += f" {random.choice(self.emoji)}"
        
        return casual_response
    
    def _extract_key_info(self, text):
        """
        Ekstrak informasi penting dari teks panjang
        
        Args:
            text (str): Teks asli
            
        Returns:
            list: Daftar informasi penting
        """
        # Pecah menjadi kalimat
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter dan singkatkan kalimat
        key_info = []
        for sentence in sentences:
            # Pisahkan awalan yang tidak penting
            cleaned = re.sub(r'^(Terima kasih|Mohon maaf|Baik|Silakan|Selamat)[,\s]+', '', sentence)
            
            # Hilangkan kata sambung dan preposisi di awal
            cleaned = re.sub(r'^(Untuk|Dengan|Oleh|Pada|Dalam|Dari)[,\s]+', '', cleaned)
            
            # Potong jika terlalu panjang
            words = cleaned.split()
            if len(words) > 10:
                cleaned = ' '.join(words[:10]) + ('...' if random.random() < 0.3 else '')
            
            if cleaned and len(cleaned) > 10:  # Minimal 10 karakter
                key_info.append(cleaned)
        
        # Jika tidak ada info penting terdeteksi, gunakan default
        if not key_info:
            key_info = ["bisa diatur kok", "langsung tanya admin aja"]
        
        return key_info

# Contoh penggunaan:
# regenerator = ResponseRegenerator()
# original_response = "Untuk bergabung dengan platform investasi seperti JTRADE, biasanya ada syarat modal awal yang bervariasi. Umumnya, jumlah minimal bisa mulai dari Rp. 100.000 hingga Rp. 1.000.000 tergantung kebijakan perusahaan dan jenis akun yang Anda pilih."
# casual_response = regenerator.regenerate(original_response, "Modal awal brp bang?", "fahrul")
# print(casual_response)
