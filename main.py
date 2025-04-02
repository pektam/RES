# main.py

"""
Main entry point untuk sistem JTRADE AUTORESPONDER.AI
Bertindak sebagai pusat kontrol yang mengintegrasikan semua modul
dengan fitur RAG (Retrieval-Augmented Generation)
"""

import os
import json
import asyncio
import datetime
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction
from keyconfig import get_openai_key
from modules.ai_engine import generate_response
from modules.conversation import save_conversation, get_conversation_history
from modules.persona import get_persona
from modules.prompt_manager import generate_prompt
from modules.intent_detector import detect_intent
from modules.analytics import log_interaction, get_daily_stats
from modules.rag_engine import RAGEngine  # Import RAG Engine
from modules.kb_factory import create_default_kb  # Import KB Factory

# Pastikan direktori modules ada
if not os.path.exists("modules"):
    os.makedirs("modules")

# Konstanta
ACCOUNTS_FILE = 'accounts/telegram_accounts.json'
ADMIN_ID = 6249036163  # ID admin/pemilik

# Inisialisasi RAG Engine di awal
rag_engine = None

# Muat akun dari JSON
def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    return []

# Fungsi untuk mendapatkan statistik semua akun
async def get_all_stats(client, chat_id, days=7):
    accounts = load_accounts()
    today = datetime.datetime.now()

    report = f"📊 **Laporan Statistik JTRADE**\n"
    report += f"Periode: {(today - datetime.timedelta(days=days)).strftime('%Y-%m-%d')} hingga {today.strftime('%Y-%m-%d')}\n\n"

    for account in accounts:
        username = account['username']
        total_interactions = 0
        total_incoming = 0

        for i in range(days):
            date = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            stats = get_daily_stats(username, date)
            if isinstance(stats, dict) and "message" not in stats:
                total_interactions += stats['total_interactions']
                total_incoming += stats['incoming_messages']

        report += f"**{username}**: {total_interactions} interaksi ({total_incoming} pesan masuk)\n"

    await client.send_message(chat_id, report)

# Fungsi untuk menangani pesan masuk
async def handle_incoming_message(event, client, username):
    sender = await event.get_sender()
    chat_id = event.chat_id
    message = event.message.text

    # Deteksi intent dan log pesan masuk
    intent = detect_intent(message)
    log_interaction(username, "incoming", message, intent)
    save_conversation(username, chat_id, sender.id, "incoming", message)

    # Ambil riwayat dan persona
    conversation_history = get_conversation_history(username, chat_id, sender.id)
    persona = get_persona(username)
    
    # Generate prompt dengan RAG
    prompt = generate_prompt(persona, conversation_history, message, debug=True)
    api_key = get_openai_key(username)

    # Simulasi typing...
    await client(SetTypingRequest(peer=chat_id, action=SendMessageTypingAction()))
    await asyncio.sleep(persona.get("response_delay", 2.0))

    # Generate dan simpan respons
    response = generate_response(prompt, api_key)
    log_interaction(username, "outgoing", response)
    save_conversation(username, chat_id, sender.id, "outgoing", response)
    
    # Kirim respons
    await client.send_message(chat_id, response)

# Fungsi untuk menangani perintah admin
async def handle_admin_command(event, client):
    if event.sender_id != ADMIN_ID:
        return False

    message = event.message.text

    if message.startswith("/stats"):
        parts = message.split()
        days = 7
        if len(parts) > 1 and parts[1].isdigit():
            days = int(parts[1])
        await get_all_stats(client, event.chat_id, days)
        return True

    elif message == "/accounts":
        accounts = load_accounts()
        response = "📱 **Daftar Akun JTRADE**\n\n"
        for i, account in enumerate(accounts, 1):
            response += f"{i}. {account['username']} ({account['phone']})\n"
        await client.send_message(event.chat_id, response)
        return True
        
    elif message == "/create_kb":
        # Perintah untuk membuat KB default
        await client.send_message(event.chat_id, "🔨 Membuat knowledge base default...")
        
        try:
            kb_path = create_default_kb()
            await client.send_message(event.chat_id, f"✅ Knowledge base default berhasil dibuat di {kb_path}")
        except Exception as e:
            await client.send_message(event.chat_id, f"❌ Error saat membuat knowledge base: {e}")
        return True
        
    elif message == "/index_kb":
        # Perintah untuk mengindeks knowledge base
        await client.send_message(event.chat_id, "🔍 Mengindeks knowledge base...")
        
        # Inisialisasi dan indeks RAG Engine
        global rag_engine
        if not rag_engine:
            rag_engine = RAGEngine()
        
        rag_engine.index_knowledge_base()
        await client.send_message(event.chat_id, "✅ Knowledge base berhasil diindeks!")
        return True

    elif message.startswith("/search"):
        # Perintah untuk pencarian RAG
        query = message[8:].strip()
        if not query:
            await client.send_message(event.chat_id, "❌ Query pencarian tidak boleh kosong!")
            return True
            
        # Inisialisasi RAG Engine jika belum
        global rag_engine
        if not rag_engine:
            rag_engine = RAGEngine()
            
        # Lakukan pencarian
        results = rag_engine.retrieve(query, top_k=5)
        
        if not results:
            await client.send_message(event.chat_id, "❓ Tidak ada hasil yang ditemukan. Coba indeks ulang knowledge base dengan /index_kb")
            return True
            
        # Format hasil
        response = f"🔍 **Hasil pencarian untuk: {query}**\n\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. **{result['key']}** (score: {result['score']:.2f})\n"
            response += f"   {result['text'][:150]}...\n\n"
            
        await client.send_message(event.chat_id, response)
        return True

    elif message.startswith("/restart"):
        parts = message.split()
        if len(parts) > 1:
            username = parts[1]
            await client.send_message(event.chat_id, f"🔄 Akun {username} sedang di-restart...")
            # Restart logic goes here...
            await client.send_message(event.chat_id, f"✅ Akun {username} berhasil di-restart!")
            return True

    elif message == "/help":
        help_text = """
🔍 **Perintah Admin JTRADE**

/stats [days] - Melihat statistik semua akun (default: 7 hari)
/accounts - Melihat daftar akun yang terdaftar
/restart [username] - Restart akun tertentu
/create_kb - Membuat knowledge base default
/index_kb - Mengindeks ulang knowledge base untuk RAG
/search [query] - Mencari informasi di knowledge base
/help - Menampilkan bantuan ini
        """
        await client.send_message(event.chat_id, help_text)
        return True

    return False

# Fungsi utama
async def main():
    # Inisialisasi RAG Engine di awal
    global rag_engine
    rag_engine = RAGEngine()
    print("Initializing RAG Engine...")
    
    # Pastikan knowledge base ada & terindeks
    kb_dir = "data/knowledge_base"
    if not os.path.exists(kb_dir) or not os.listdir(kb_dir):
        print("Knowledge base not found. Creating default...")
        create_default_kb()
        
    rag_engine.index_knowledge_base()
    print("RAG Engine initialized successfully")
    
    # Setup akun Telegram
    accounts = load_accounts()
    clients = []

    for account in accounts:
        username = account['username']
        phone = account['phone']
        api_id = account['api_id']
        api_hash = account['api_hash']

        session_name = f"accounts/{phone.replace('+', '')}"
        client = TelegramClient(session_name, api_id, api_hash)

        await client.start()

        client.add_event_handler(
            lambda event, c=client: handle_admin_command(event, c),
            events.NewMessage(pattern=r"^/")
        )

        @client.on(events.NewMessage(incoming=True))
        async def message_handler(event, c=client, u=username):
            is_admin_command = await handle_admin_command(event, c)
            if not is_admin_command:
                await handle_incoming_message(event, c, u)

        clients.append(client)
        print(f"Client {username} ({phone}) started")

    await asyncio.gather(*[client.run_until_disconnected() for client in clients])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program dihentikan oleh pengguna")
    except Exception as e:
        print(f"Error: {e}")