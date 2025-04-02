# modules/knowledge_base.py

"""
Modul untuk mengelola knowledge base
Menyediakan informasi dan FAQ tentang JTRADE
"""

import os
import json

# Pastikan direktori knowledge_base ada
if not os.path.exists("data/knowledge_base"):
    os.makedirs("data/knowledge_base")

def get_knowledge(topic=None):
    """
    Ambil informasi dari knowledge base
    
    Args:
        topic (str, optional): Topik spesifik yang diinginkan
        
    Returns:
        dict: Data dari knowledge base
    """
    # File untuk knowledge base umum
    general_kb_file = "data/knowledge_base/general.json"
    
    # Jika file tidak ada, buat dengan data default
    if not os.path.exists(general_kb_file):
        default_kb = {
            "company_info": {
                "name": "JTRADE",
                "description": "Platform investasi modern yang fokus pada pengalaman investor",
                "unique_selling_points": [
                    "Biaya transaksi terendah di industri",
                    "Eksekusi order tercepat",
                    "Analisis pasar real-time",
                    "Layanan personal oleh financial advisor berpengalaman"
                ]
            },
            "products": {
                "stock_trading": {
                    "description": "Perdagangan saham dengan komisi terendah di pasar",
                    "features": ["Real-time quotes", "Advanced charting", "Research reports"]
                },
                "mutual_funds": {
                    "description": "Investasi reksa dana tanpa biaya pembelian",
                    "features": ["Seleksi reksa dana terbaik", "Analisis kinerja mendalam"]
                },
                "bonds": {
                    "description": "Investasi obligasi pemerintah dan korporasi",
                    "features": ["Yield kompetitif", "Analisis credit rating"]
                }
            },
            "faq": [
                {
                    "question": "Berapa minimum deposit di JTRADE?",
                    "answer": "Minimum deposit di JTRADE adalah Rp 1.000.000 untuk membuka akun reguler."
                },
                {
                    "question": "Bagaimana cara membuka akun di JTRADE?",
                    "answer": "Membuka akun di JTRADE sangat mudah. Anda cukup mengunduh aplikasi kami, melengkapi formulir pendaftaran online, dan mengunggah dokumen identitas. Proses verifikasi biasanya selesai dalam 1 hari kerja."
                },
                {
                    "question": "Apa saja biaya transaksi di JTRADE?",
                    "answer": "JTRADE menawarkan biaya transaksi terendah di industri, mulai dari 0.1% untuk transaksi saham dan gratis untuk pembelian reksa dana."
                }
            ]
        }
        
        with open(general_kb_file, "w") as f:
            json.dump(default_kb, f, indent=4)
    
    # Baca knowledge base
    with open(general_kb_file, "r") as f:
        knowledge_base = json.load(f)
    
    # Jika topic ditentukan, ambil hanya bagian tersebut
    if topic and topic in knowledge_base:
        return knowledge_base[topic]
    
    return knowledge_base