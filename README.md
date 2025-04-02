# JTRADE AUTORESPONDER.AI 🤖💼

## Deskripsi Proyek
JTRADE AUTORESPONDER.AI adalah platform AI canggih untuk manajemen interaksi dan layanan keuangan berbasis Telegram, dirancang untuk memberikan respons cerdas dan personal kepada investor.

## Fitur Utama
- 🔍 Deteksi Intent Percakapan
- 🤖 Persona AI Dinamis
- 💬 Manajemen Percakapan Cerdas
- 📊 Analitik Interaksi Mendalam
- 🧠 Retrieval-Augmented Generation (RAG)

## Struktur Proyek
```
PROJECTRE/
│
├── accounts/          # Manajemen akun Telegram
├── data/              # Penyimpanan data
│   ├── analytics/     # Data analitik
│   ├── conversations/ # Riwayat percakapan
│   ├── knowledge_base/# Basis pengetahuan
│   └── ...
│
├── modules/           # Modul utama sistem
│   ├── ai_engine.py   # Integrasi AI
│   ├── analytics.py   # Analitik interaksi
│   ├── persona.py     # Manajemen persona
│   └── ...
│
├── persona/           # Konfigurasi persona
│   ├── contexts/      # Konteks komunikasi
│   ├── personalities/ # Tipe kepribadian
│   └── styles/        # Gaya komunikasi
│
└── main.py            # Entry point sistem
```

## Prasyarat
- Python 3.8+
- Library: Telethon, OpenAI, NumPy
- Akun Telegram Developer
- OpenAI API Key

## Instalasi
1. Clone repositori
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Konfigurasi `.env` dengan API keys
4. Jalankan `telegram_login.py` untuk setup akun

## Penggunaan
```bash
python main.py
```

## Kontribusi
Silakan baca `CONTRIBUTING.md` untuk detail panduan kontribusi.

## Lisensi
Proyek ini dilisensikan di bawah [TAMBAHKAN LISENSI].

## Kontak
- Email: info@jtrade.id
- Telegram: @JTRADESupport
```
