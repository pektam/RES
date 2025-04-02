# keyconfig.py

# Modul ini digunakan untuk memanggil OPENAI_API_KEY dari file .env
# berdasarkan username yang disimpan di telegram_accounts.json

import os
from dotenv import load_dotenv

# Muat file .env
load_dotenv()

def get_openai_key(username: str) -> str:
    """
    Ambil OPENAI_API_KEY berdasarkan username.
    Contoh: jika username = 'fahrul', maka akan ambil OPENAI_API_FAHRUL dari .env
    """
    key_name = f"OPENAI_API_{username.upper()}"
    return os.getenv(key_name)