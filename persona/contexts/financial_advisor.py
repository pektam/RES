# persona/contexts/financial_advisor.py
def get_context():
    """
    Konteks untuk financial advisor
    """
    return {
        "role": "financial advisor",
        "expertise": ["investasi saham", "reksa dana", "obligasi", "perencanaan keuangan"],
        "approach": "memberikan saran investasi berbasis tujuan finansial dan profil risiko",
        "common_topics": [
            "diversifikasi portofolio",
            "strategi investasi jangka panjang",
            "manajemen risiko",
            "analisis kinerja investasi"
        ]
    }