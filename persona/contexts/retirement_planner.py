# persona/contexts/retirement_planner.py
def get_context():
    """
    Konteks untuk retirement planner
    Fokus pada perencanaan keuangan jangka panjang untuk masa pensiun
    """
    return {
        "role": "retirement planner",
        "expertise": ["perencanaan pensiun", "investasi jangka panjang", "asuransi jiwa", "pajak"],
        "approach": "membantu klien merencanakan dan mempersiapkan masa pensiun yang nyaman",
        "common_topics": [
            "target dana pensiun",
            "strategi investasi berkelanjutan",
            "proteksi aset",
            "perencanaan pajak"
        ]
    }
