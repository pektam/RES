# modules/ai_engine.py

"""
Engine AI untuk JTRADE
Modul ini menangani koneksi ke OpenAI API dan menghasilkan respons
berdasarkan prompt yang diberikan.
"""

import openai
import time

def generate_response(prompt, api_key, max_retries=3):
    """
    Generate respons dari OpenAI API berdasarkan prompt
    
    Args:
        prompt (str): Prompt yang akan dikirim ke API
        api_key (str): OpenAI API key
        max_retries (int): Jumlah percobaan ulang jika terjadi error
        
    Returns:
        str: Respons dari API
    """
    openai.api_key = api_key
    
    # Implementasi retry dengan exponential backoff
    retry = 0
    while retry < max_retries:
        try:
            # Gunakan API OpenAI untuk mendapatkan respons
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Atau model lain yang diinginkan
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            # Ambil teks respons
            return response.choices[0].message.content
            
        except Exception as e:
            retry += 1
            # Exponential backoff - tunggu 2^retry detik sebelum mencoba lagi
            wait_time = 2 ** retry
            print(f"Error calling OpenAI API: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    # Jika semua percobaan gagal, kembalikan pesan error
    return "Maaf, saya sedang mengalami masalah teknis. Silakan coba lagi nanti."
