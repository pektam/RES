# modules/kb_factory.py

"""
Knowledge Base Factory untuk JTRADE AUTORESPONDER.AI
Membuat dan mengelola knowledge base dari berbagai sumber
"""

import os
import json
import datetime
from pathlib import Path

# Pastikan direktori ada
KB_DIR = "data/knowledge_base"
if not os.path.exists(KB_DIR):
    os.makedirs(KB_DIR)

class KnowledgeBaseFactory:
    """
    Factory untuk membuat knowledge base dengan modular approach
    """
    
    def __init__(self):
        self.sources = {}
        
    def register_source(self, source_name, data):
        """Daftarkan sumber data ke factory"""
        self.sources[source_name] = data
    
    def build_kb(self, kb_name, sources=None):
        """Buat knowledge base dari sumber yang terdaftar"""
        if sources is None:
            sources = list(self.sources.keys())
        
        # Buat struktur KB
        kb = {
            "metadata": {
                "created_at": datetime.datetime.now().isoformat(),
                "sources": sources,
                "version": "1.0"
            }
        }
        
        # Tambahkan data dari setiap sumber
        for source in sources:
            if source in self.sources:
                kb[source] = self.sources[source]
        
        # Simpan ke file
        file_path = os.path.join(KB_DIR, f"{kb_name}.json")
        with open(file_path, 'w') as f:
            json.dump(kb, f, indent=4)
        
        print(f"Knowledge base '{kb_name}' berhasil dibuat di {file_path}")
        return file_path
    
    @staticmethod
    def from_product_data(products_data):
        """Buat factory dengan data produk"""
        factory = KnowledgeBaseFactory()
        factory.register_source("products", products_data)
        return factory
    
    @staticmethod
    def from_faq(faqs):
        """Buat factory dengan data FAQ"""
        factory = KnowledgeBaseFactory()
        factory.register_source("faq", faqs)
        return factory
    
    @staticmethod
    def from_company_info(company_data):
        """Buat factory dengan informasi perusahaan"""
        factory = KnowledgeBaseFactory()
        factory.register_source("company_info", company_data)
        return factory
    
    @staticmethod
    def combine_factories(*factories):
        """Gabungkan beberapa factory menjadi satu"""
        combined = KnowledgeBaseFactory()
        
        for factory in factories:
            for source_name, data in factory.sources.items():
                combined.register_source(source_name, data)
        
        return combined

def create_default_kb():
    """
    Buat knowledge base default untuk JTRADE
    """
    # Data produk
    products = {
        "stock_trading": {
            "description": "Perdagangan saham dengan komisi terendah di pasar",
            "features": ["Real-time quotes", "Advanced charting", "Research reports"],
            "minimum_deposit": "Rp 1.000.000",
            "fees": "0.1% per transaksi, minimum Rp 10.000"
        },
        "mutual_funds": {
            "description": "Investasi reksa dana tanpa biaya pembelian",
            "features": ["Seleksi reksa dana terbaik", "Analisis kinerja mendalam"],
            "minimum_investment": "Rp 500.000",
            "fees": "0% biaya pembelian, 0.5-2% biaya pengelolaan tahunan"
        },
        "bonds": {
            "description": "Investasi obligasi pemerintah dan korporasi",
            "features": ["Yield kompetitif", "Analisis credit rating"],
            "minimum_investment": "Rp 1.000.000",
            "fees": "0.1% biaya transaksi"
        }
    }
    
    # FAQ
    faqs = [
        {
            "question": "Berapa minimum deposit di JTRADE?",
            "answer": "Minimum deposit di JTRADE adalah Rp 1.000.000 untuk membuka akun reguler."
        },
        {
            "question": "Bagaimana cara membuka akun di JTRADE?",
            "answer": "Membuka akun di JTRADE sangat mudah. Anda cukup mengunduh aplikasi kami, melengkapi formulir pendaftaran online, dan mengunggah dokumen identitas."
        },
        {
            "question": "Apa saja biaya transaksi di JTRADE?",
            "answer": "JTRADE menawarkan biaya transaksi terendah di industri, mulai dari 0.1% untuk transaksi saham dan gratis untuk pembelian reksa dana."
        },
        {
            "question": "Apakah JTRADE menyediakan analisis pasar?",
            "answer": "Ya, JTRADE menyediakan analisis pasar komprehensif, termasuk laporan riset, grafik teknikal, dan rekomendasi saham."
        }
    ]
    
    # Informasi perusahaan
    company_info = {
        "name": "JTRADE",
        "description": "Platform investasi modern yang fokus pada pengalaman investor",
        "founded": "2020",
        "headquarters": "Jakarta, Indonesia",
        "unique_selling_points": [
            "Biaya transaksi terendah di industri",
            "Eksekusi order tercepat",
            "Analisis pasar real-time",
            "Layanan personal oleh financial advisor berpengalaman"
        ],
        "contact": {
            "email": "info@jtrade.id",
            "phone": "+6221123456",
            "address": "Jl. Sudirman No. 123, Jakarta Pusat"
        }
    }
    
    # Buat factory dan knowledge base
    factory = KnowledgeBaseFactory()
    factory.register_source("products", products)
    factory.register_source("faq", faqs)
    factory.register_source("company_info", company_info)
    
    return factory.build_kb("general")

def create_kb_from_dir(dir_path, kb_name="custom"):
    """
    Buat knowledge base dari direktori dengan file JSON
    """
    factory = KnowledgeBaseFactory()
    
    # Cari semua file JSON di direktori
    for file_path in Path(dir_path).glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Gunakan nama file sebagai nama sumber
            source_name = file_path.stem
            factory.register_source(source_name, data)
            print(f"Loaded {source_name} from {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    # Buat knowledge base
    return factory.build_kb(kb_name)