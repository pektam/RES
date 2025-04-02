# modules/conversation.py

"""
Modul untuk mengelola riwayat percakapan
Menyimpan dan mengambil riwayat chat untuk referensi dalam menghasilkan respons
"""

import os
import json
import datetime

# Pastikan direktori data ada
if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists("data/conversations"):
    os.makedirs("data/conversations")

def save_conversation(username, chat_id, user_id, message_type, message):
    """
    Simpan pesan ke riwayat percakapan
    
    Args:
        username (str): Username akun JTRADE
        chat_id (int): ID chat Telegram
        user_id (int): ID pengguna yang berinteraksi
        message_type (str): Jenis pesan ('incoming' atau 'outgoing')
        message (str): Isi pesan
    """
    # Format nama file berdasarkan username dan ID
    filename = f"data/conversations/{username}_{chat_id}_{user_id}.json"
    
    # Buat struktur data untuk pesan
    new_message = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": message_type,
        "content": message
    }
    
    # Muat riwayat yang ada atau buat baru jika belum ada
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            history = json.load(f)
    else:
        history = []
    
    # Tambahkan pesan baru
    history.append(new_message)
    
    # Simpan kembali ke file
    with open(filename, 'w') as f:
        json.dump(history, f, indent=4)

def get_conversation_history(username, chat_id, user_id, max_messages=10):
    """
    Ambil riwayat percakapan
    
    Args:
        username (str): Username akun JTRADE
        chat_id (int): ID chat Telegram
        user_id (int): ID pengguna yang berinteraksi
        max_messages (int): Jumlah maksimum pesan yang diambil
        
    Returns:
        list: Daftar pesan dalam riwayat percakapan
    """
    filename = f"data/conversations/{username}_{chat_id}_{user_id}.json"
    
    if not os.path.exists(filename):
        return []
    
    with open(filename, 'r') as f:
        history = json.load(f)
    
    # Ambil n pesan terakhir
    return history[-max_messages:]