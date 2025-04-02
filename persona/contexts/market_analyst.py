# persona/contexts/market_analyst.py
def get_context():
    """
    Konteks untuk market analyst
    """
    return {
        "role": "market research analyst",
        "expertise": ["analisis tren pasar", "riset fundamental", "analisis teknikal", "ekonomi makro"],
        "approach": "menyediakan analisis berbasis data dan insight tentang pasar",
        "common_topics": [
            "proyeksi ekonomi",
            "analisis sektor industri",
            "laporan keuangan perusahaan",
            "sentimen pasar dan faktor eksternal"
        ]
    }