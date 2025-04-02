# telegram_login.py

"""
Skrip ini digunakan untuk:
- Login ke akun Telegram menggunakan Telethon
- Menyimpan akun Telegram ke file JSON (accounts/telegram_accounts.json)
- Menyimpan OPENAI_API_KEY ke file .env menggunakan format: OPENAI_API_{USERNAME}
- Mengakses API key dengan modul `keyconfig.py` agar tidak langsung akses .env

Struktur data:
- .env     → menyimpan API key (OPENAI_API_KEY)
- JSON     → menyimpan data akun (username, phone, api_id, api_hash, 2FA)

Catatan:
- Jangan commit .env ke repo publik
- Semua akses API key sebaiknya melalui keyconfig.get_openai_key(username)
"""


from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
import json
import os
from keyconfig import get_openai_key

# Pastikan folder 'accounts' ada
if not os.path.exists("accounts"):
    os.makedirs("accounts")

ACCOUNTS_FILE = 'accounts/telegram_accounts.json'
ENV_FILE = '.env'

# Fungsi untuk menyimpan akun
def save_accounts(accounts):
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=4)

# Fungsi untuk memuat akun
def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    return []

# Fungsi untuk menambahkan ke file .env
def append_to_env(key, value):
    with open(ENV_FILE, 'a') as f:
        f.write(f"{key}={value}\n")

# Fungsi login
def login_account(api_id, api_hash, phone, password_2fa=None):
    session_name = f"accounts/{phone.replace('+', '')}"
    client = TelegramClient(session_name, api_id, api_hash)
    client.connect()

    if not client.is_user_authorized():
        print(f"Mengirim kode verifikasi ke {phone}...")
        client.send_code_request(phone)
        code = input(f"Masukkan kode verifikasi untuk {phone}: ")
        try:
            client.sign_in(phone, code)
        except SessionPasswordNeededError:
            if password_2fa:
                client.sign_in(password=password_2fa)
            else:
                password = input("Masukkan password 2FA: ")
                client.sign_in(password=password)

    me = client.get_me()
    print(f"Berhasil login sebagai {me.first_name} ({phone})")
    return client

# Program utama

def main():
    accounts = load_accounts()

    while True:
        print("\n=== MENU TELEGRAM LOGIN ===")
        print("1. Login ke semua akun")
        print("2. Tambah akun baru")
        print("3. Lihat daftar akun")
        print("4. Keluar")

        choice = input("Pilih menu (1-4): ")

        if choice == '1':
            if not accounts:
                print("Belum ada akun yang tersimpan.")
                continue
            clients = []
            for account in accounts:
                client = login_account(
                    account['api_id'],
                    account['api_hash'],
                    account['phone'],
                    account.get('password_2fa')
                )
                clients.append(client)
            print(f"Berhasil login ke {len(clients)} akun.")
            input("Tekan Enter untuk kembali ke menu...")
            for client in clients:
                client.disconnect()

        elif choice == '2':
            print("\n=== Tambah Akun Baru ===")
            username = input("Masukkan username unik akun (tanpa spasi): ").strip().lower()
            phone = input("Masukkan nomor telepon (format: +628xxxxxxxx): ").strip()
            api_id = input("Masukkan API ID Telegram: ").strip()
            api_hash = input("Masukkan API Hash Telegram: ").strip()
            openai_api_key = input("Masukkan OPENAI API KEY: ").strip()
            password_2fa = input("Masukkan password 2FA (kosongkan jika tidak ada): ").strip()

            # Tambahkan ke .env
            env_key = f"OPENAI_API_{username.upper()}"
            append_to_env(env_key, openai_api_key)

            # Simpan ke JSON
            accounts.append({
                "username": username,
                "phone": phone,
                "api_id": api_id,
                "api_hash": api_hash,
                "password_2fa": password_2fa
            })
            save_accounts(accounts)
            print(f"Akun {phone} berhasil ditambahkan!")

        elif choice == '3':
            if not accounts:
                print("Belum ada akun yang tersimpan.")
            else:
                print("\nDaftar Akun:")
                for i, account in enumerate(accounts, 1):
                    print(f"{i}. {account['username']} - {account['phone']}")

        elif choice == '4':
            print("Terima kasih telah menggunakan program ini.")
            break

        else:
            print("Pilihan tidak valid. Silakan pilih 1-4.")

if __name__ == "__main__":
    main()