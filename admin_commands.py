# admin_commands.py

"""
Script untuk pemantauan dan pengelolaan sistem JTRADE
Menyediakan utilitas untuk admin/pemilik perusahaan
"""

import json
import os
import datetime
from modules.analytics import get_daily_stats

def show_active_accounts():
    """
    Menampilkan daftar akun yang aktif
    """
    accounts_file = 'accounts/telegram_accounts.json'
    
    if not os.path.exists(accounts_file):
        print("File akun tidak ditemukan.")
        return
    
    with open(accounts_file, 'r') as f:
        accounts = json.load(f)
    
    print("\n=== Daftar Akun Aktif ===")
    print(f"{'No.':<5}{'Username':<15}{'Phone':<15}")
    print("-" * 35)
    
    for i, account in enumerate(accounts, 1):
        print(f"{i:<5}{account['username']:<15}{account['phone']:<15}")

def generate_report(username=None, days=7):
    """
    Membuat laporan statistik
    
    Args:
        username (str, optional): Username akun tertentu, atau None untuk semua akun
        days (int, optional): Jumlah hari ke belakang untuk laporan
    """
    today = datetime.datetime.now()
    
    # Jika username tidak ditentukan, cari semua akun
    if username is None:
        accounts_file = 'accounts/telegram_accounts.json'
        if os.path.exists(accounts_file):
            with open(accounts_file, 'r') as f:
                accounts = json.load(f)
            usernames = [account['username'] for account in accounts]
        else:
            print("File akun tidak ditemukan.")
            return
    else:
        usernames = [username]
    
    # Header report
    print("\n=== Laporan Interaksi ===")
    print(f"Periode: {(today - datetime.timedelta(days=days)).strftime('%Y-%m-%d')} hingga {today.strftime('%Y-%m-%d')}")
    print("-" * 60)
    
    # Report untuk setiap akun
    for username in usernames:
        print(f"\nAkun: {username}")
        print("-" * 20)
        
        total_interactions = 0
        total_incoming = 0
        total_outgoing = 0
        all_intents = {}
        
        # Ambil data untuk setiap hari
        for i in range(days):
            date = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            stats = get_daily_stats(username, date)
            
            if isinstance(stats, dict) and "message" not in stats:
                # Cetak statistik harian
                print(f"{date}: {stats['total_interactions']} interaksi ({stats['incoming_messages']} in, {stats['outgoing_messages']} out)")
                
                # Akumulasi total
                total_interactions += stats['total_interactions']
                total_incoming += stats['incoming_messages']
                total_outgoing += stats['outgoing_messages']
                
                # Gabungkan intent
                for intent, count in stats.get('intent_distribution', {}).items():
                    if intent in all_intents:
                        all_intents[intent] += count
                    else:
                        all_intents[intent] = count
        
        # Cetak summary
        print(f"\nTotal {days} hari terakhir: {total_interactions} interaksi")
        print(f"Rata-rata: {total_interactions/days:.1f} interaksi per hari")
        
        # Cetak distribusi intent
        if all_intents:
            print("\nIntent yang paling umum:")
            sorted_intents = sorted(all_intents.items(), key=lambda x: x[1], reverse=True)
            for intent, count in sorted_intents[:5]:
                print(f"- {intent}: {count} kali")

def restart_account(username):
    """
    Restart sesi akun tertentu
    
    Args:
        username (str): Username akun yang akan di-restart
    """
    # Untuk implementasi sebenarnya, ini akan me-restart client Telegram
    # Di sini hanya simulasi untuk demonstrasi
    print(f"\nRestart akun {username}...")
    print(f"Akun {username} berhasil di-restart")

def main():
    """
    Menu utama admin commands
    """
    while True:
        print("\n=== JTRADE Admin Menu ===")
        print("1. Tampilkan Akun Aktif")
        print("2. Buat Laporan Statistik")
        print("3. Restart Akun")
        print("4. Keluar")
        
        choice = input("Pilih menu (1-4): ")
        
        if choice == '1':
            show_active_accounts()
        
        elif choice == '2':
            print("\n=== Menu Laporan ===")
            print("1. Semua Akun")
            print("2. Akun Tertentu")
            report_choice = input("Pilih opsi (1-2): ")
            
            days = input("Berapa hari ke belakang? (default: 7): ")
            days = int(days) if days.isdigit() else 7
            
            if report_choice == '1':
                generate_report(days=days)
            elif report_choice == '2':
                username = input("Masukkan username akun: ")
                generate_report(username=username, days=days)
        
        elif choice == '3':
            show_active_accounts()
            username = input("Masukkan username akun yang akan di-restart: ")
            restart_account(username)
        
        elif choice == '4':
            print("Keluar dari admin menu.")
            break
        
        else:
            print("Pilihan tidak valid. Silakan pilih 1-4.")

if __name__ == "__main__":
    main()