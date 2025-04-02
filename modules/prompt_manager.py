import os
import json
import time
from modules.knowledge_base import get_knowledge
from modules.intent_detector import detect_intent

def generate_prompt(persona, conversation_history, latest_message, debug=False):
    """
    Generate prompt untuk OpenAI API berdasarkan persona, riwayat percakapan, dan intent

    Args:
        persona (dict): Informasi persona
        conversation_history (list): Riwayat percakapan
        latest_message (str): Pesan terbaru dari pengguna
        debug (bool): Jika True, tampilkan prompt dan estimasi token

    Returns:
        str: Prompt untuk dikirim ke OpenAI API
    """
    intents = detect_intent(latest_message)
    knowledge = get_knowledge()

    # Template berdasarkan style persona
    def get_prompt_template(style, persona):
        style_prompts = {
            "santai": {
                "system": (
                    "Lu lagi jadi {name}! Anak {context} dari JTRADE yang santuy tapi paham cuan. "
                    "Ngomongnya ngalir aja kayak ngobrol di tongkrongan."
                ),
                "instruction": "Jawab singkat-singkat aja, bro. Jangan lebay, yang penting nyambung!"
            },
            "formal": {
                "system": (
                    "Anda sedang berperan sebagai {name}, seorang {context} profesional dari JTRADE. "
                    "Gunakan bahasa sopan dan informatif sesuai etika komunikasi bisnis."
                ),
                "instruction": "Sampaikan jawaban secara ringkas, padat, dan jelas. Hindari bahasa informal."
            },
            "ramah": {
                "system": (
                    "Kamu lagi jadi {name}, si {context} dari JTRADE yang super friendly. "
                    "Selalu kasih respon yang bikin user merasa disambut hangat!"
                ),
                "instruction": "Balas dengan 1-2 kalimat yang ramah banget, biar user ngerasa ditemenin."
            },
            "ngakak": {
                "system": (
                    "Lo tuh {name}, si {context} dari JTRADE yang suka ngelawak tapi tetep paham cuan. "
                    "Bikin user ketawa tapi tetep dapet insight."
                ),
                "instruction": "Bikin jawabannya lucu dikit, 1-2 kalimat aja, jangan garing ya!"
            },
            "deep": {
                "system": (
                    "Sekarang lo jadi {name}, {context} dari JTRADE yang ngomongnya dalem dan mikir. "
                    "Suarakan insight yang bisa nyentil tapi tetep simpel."
                ),
                "instruction": "Jawaban pendek tapi dalem. 1-2 kalimat yang bisa bikin mikir."
            }
        }
        return style_prompts.get(style, style_prompts["santai"])

    style = persona.get("style", "santai")
    selected_template = get_prompt_template(style, persona)

    template = {
        "system": selected_template["system"].format(**persona),
        "instruction": selected_template["instruction"],
        "intent_info": "",
        "history": "",
        "latest_message": latest_message.strip()
    }

    # Ambil informasi intent terbatas
    if 'inquiry_product' in intents:
        products = list(knowledge.get('products', {}).items())[:2]
        lines = ["Informasi produk yang relevan:"]
        for name, data in products:
            lines.append(f"- {name}: {data['description']}")
        template['intent_info'] += "\n" + "\n".join(lines)

    if 'inquiry_fee' in intents or 'inquiry_registration' in intents:
        faqs = knowledge.get('faq', [])
        filtered = [f for f in faqs if any(k in f['question'].lower() for k in ['biaya', 'fee', 'daftar', 'buka akun'])][:2]
        for faq in filtered:
            template['intent_info'] += f"\n- {faq['question']}: {faq['answer']}"

    # Tambahkan RAG knowledge
    template['rag_knowledge'] = get_relevant_knowledge(
        persona=persona,
        query=latest_message,
        intent=intents,
        max_tokens=300
    )

    # Format riwayat percakapan
    recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
    formatted = []
    for msg in recent_history:
        if isinstance(msg, dict) and 'user' in msg and 'assistant' in msg:
            formatted.append(f"User: {msg['user']}\nAssistant: {msg['assistant']}")
        else:
            formatted.append(str(msg))
    template['history'] = "\n".join(formatted)

    # Gabungkan semua termasuk RAG
    full_prompt = (
        f"{template['system']}\n\n"
        f"{template['instruction']}\n\n"
        f"{template['intent_info']}\n"
        f"{template['rag_knowledge']}\n"
        f"Percakapan sebelumnya:\n{template['history']}\n\n"
        f"User: {template['latest_message']}\nAssistant:"
    )

    # Debug log
    if debug:
        print("\n---[ Prompt Debug Start ]---")
        print(full_prompt)
        token_estimate = len(full_prompt.split()) * 1.3
        print(f"\n[Typing simulation...]\nToken Estimate: ~{int(token_estimate)} tokens")
        print("---[ Prompt Debug End ]---\n")
        time.sleep(1.2)

    return full_prompt

# Fungsi helper untuk RAG
def get_relevant_knowledge(persona, query, intent=None, max_tokens=300):
    """
    Mendapatkan knowledge yang relevan dari RAG engine

    Args:
        persona (dict): Informasi persona
        query (str): Query dari pengguna
        intent (dict, optional): Intent yang terdeteksi
        max_tokens (int): Estimasi batas token

    Returns:
        str: Bagian prompt dengan informasi relevan
    """
    # Placeholder - fungsi sebenarnya diimplementasikan di RAG Engine
    return "Informasi relevan akan disediakan oleh RAG Engine"
