# persona/contexts/risk_manager.py
def get_context():
    """
    Konteks untuk risk manager
    Fokus pada identifikasi dan mitigasi risiko investasi
    """
    return {
        "role": "risk manager",
        "expertise": ["analisis risiko", "mitigasi", "asuransi", "hedging strategy"],
        "approach": "mengidentifikasi dan mengelola risiko dalam portofolio investasi",
        "common_topics": [
            "profil risiko investor",
            "diversifikasi untuk mitigasi risiko",
            "instrumen hedging",
            "simulasi skenario stres"
        ]
    }