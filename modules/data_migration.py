# modules/data_migration.py

"""
Modul untuk migrasi dan transformasi data
Membantu mengintegrasikan data dari sistem lama atau memigrasi ke format baru
"""

import os
import json
import datetime
import csv
import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/logs/migration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('data_migration')

def create_sqlite_db():
    """
    Membuat database SQLite untuk JTRADE
    
    Returns:
        str: Path ke database
    """
    # Pastikan direktori ada
    os.makedirs("data/db", exist_ok=True)
    
    db_path = "data/db/jtrade.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            chat_id TEXT,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            first_interaction TIMESTAMP,
            last_interaction TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            chat_id TEXT,
            timestamp TIMESTAMP,
            message_type TEXT,
            content TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS intents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            intent_name TEXT,
            confidence REAL,
            FOREIGN KEY (message_id) REFERENCES messages(id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully created SQLite database at {db_path}")
        return db_path
        
    except Exception as e:
        logger.error(f"Error creating SQLite database: {str(e)}")
        return None

def import_conversations_to_db(db_path=None):
    """
    Impor data percakapan dari file JSON ke SQLite
    
    Args:
        db_path (str, optional): Path ke database SQLite
        
    Returns:
        dict: Status migrasi
    """
    if not db_path:
        db_path = "data/db/jtrade.db"
        
    if not os.path.exists(db_path):
        db_path = create_sqlite_db()
        if not db_path:
            return {"status": "error", "message": "Failed to create database"}
    
    conv_dir = "data/conversations"
    if not os.path.exists(conv_dir):
        return {"status": "error", "message": "Conversations directory not found"}
    
    results = {
        "status": "success",
        "processed_files": 0,
        "processed_messages": 0,
        "users_added": 0,
        "errors": []
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Process each JSON file
        for filepath in Path(conv_dir).glob("*.json"):
            try:
                # Parse filename
                filename = filepath.stem
                parts = filename.split('_')
                
                if len(parts) >= 3:
                    username = parts[0]
                    chat_id = parts[1]
                    user_id = parts[2]
                    
                    # Read messages
                    with open(filepath, 'r') as f:
                        messages = json.load(f)
                    
                    # If messages exist, update or insert user
                    if messages:
                        first_msg_time = messages[0].get("timestamp", None)
                        last_msg_time = messages[-1].get("timestamp", None)
                        
                        # Check if user exists
                        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                        user_exists = cursor.fetchone()
                        
                        if not user_exists:
                            # Insert new user
                            cursor.execute('''
                            INSERT INTO users (user_id, chat_id, username, first_interaction, last_interaction)
                            VALUES (?, ?, ?, ?, ?)
                            ''', (user_id, chat_id, username, first_msg_time, last_msg_time))
                            results["users_added"] += 1
                        else:
                            # Update existing user
                            cursor.execute('''
                            UPDATE users 
                            SET last_interaction = MAX(last_interaction, ?) 
                            WHERE user_id = ?
                            ''', (last_msg_time, user_id))
                        
                        # Insert messages
                        for message in messages:
                            timestamp = message.get("timestamp", None)
                            msg_type = message.get("type", "unknown")
                            content = message.get("content", "")
                            
                            cursor.execute('''
                            INSERT INTO messages (user_id, chat_id, timestamp, message_type, content)
                            VALUES (?, ?, ?, ?, ?)
                            ''', (user_id, chat_id, timestamp, msg_type, content))
                            
                            # Get message ID
                            msg_id = cursor.lastrowid
                            
                            # If it's an incoming message, check for intent
                            if msg_type == "incoming" and message.get("intent"):
                                for intent_name, confidence in message["intent"].items():
                                    cursor.execute('''
                                    INSERT INTO intents (message_id, intent_name, confidence)
                                    VALUES (?, ?, ?)
                                    ''', (msg_id, intent_name, float(confidence)))
                            
                            results["processed_messages"] += 1
                        
                    results["processed_files"] += 1
                
            except Exception as e:
                error_msg = f"Error processing {filepath}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Migration completed: {results['processed_files']} files, {results['processed_messages']} messages")
        return results
        
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        return {"status": "error", "message": str(e)}

def export_db_to_json(db_path=None, output_dir=None):
    """
    Export data dari SQLite ke format JSON
    
    Args:
        db_path (str, optional): Path ke database SQLite
        output_dir (str, optional): Direktori output
        
    Returns:
        dict: Status ekspor
    """
    if not db_path:
        db_path = "data/db/jtrade.db"
        
    if not os.path.exists(db_path):
        return {"status": "error", "message": "Database not found"}
    
    if not output_dir:
        output_dir = "data/export/db_export"
        os.makedirs(output_dir, exist_ok=True)
    
    results = {
        "status": "success",
        "users_exported": 0,
        "messages_exported": 0,
        "output_dir": output_dir
    }
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Export users
        cursor.execute("SELECT * FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        
        with open(os.path.join(output_dir, "users.json"), 'w') as f:
            json.dump(users, f, indent=4)
        
        results["users_exported"] = len(users)
        
        # Export messages per user
        for user in users:
            user_id = user["user_id"]
            
            # Get messages
            cursor.execute("""
            SELECT m.*, GROUP_CONCAT(i.intent_name || ':' || i.confidence, ', ') as intents
            FROM messages m
            LEFT JOIN intents i ON m.id = i.message_id
            WHERE m.user_id = ?
            GROUP BY m.id
            ORDER BY m.timestamp
            """, (user_id,))
            
            messages = []
            for row in cursor.fetchall():
                message = dict(row)
                
                # Parse intents if they exist
                intents_str = message.pop("intents", None)
                if intents_str:
                    intent_dict = {}
                    for intent_pair in intents_str.split(", "):
                        if ":" in intent_pair:
                            name, conf = intent_pair.split(":")
                            intent_dict[name] = float(conf)
                    message["intents"] = intent_dict
                
                messages.append(message)
            
            # Save to file
            user_filename = f"{user['username']}_{user_id}.json"
            with open(os.path.join(output_dir, user_filename), 'w') as f:
                json.dump(messages, f, indent=4)
            
            results["messages_exported"] += len(messages)
        
        conn.close()
        logger.info(f"Export completed: {results['users_exported']} users, {results['messages_exported']} messages")
        return results
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return {"status": "error", "message": str(e)}

def import_csv_to_knowledge_base(csv_path, kb_name=None):
    """
    Impor data CSV ke knowledge base
    Format CSV: key,value,category
    
    Args:
        csv_path (str): Path ke file CSV
        kb_name (str, optional): Nama knowledge base
        
    Returns:
        dict: Status impor
    """
    if not os.path.exists(csv_path):
        return {"status": "error", "message": "CSV file not found"}
    
    # Tentukan nama KB
    if not kb_name:
        # Gunakan nama file tanpa ekstensi
        kb_name = os.path.basename(csv_path).rsplit('.', 1)[0]
    
    # Path KB
    kb_dir = "data/knowledge_base"
    os.makedirs(kb_dir, exist_ok=True)
    kb_path = os.path.join(kb_dir, f"{kb_name}.json")
    
    # Inisialisasi KB
    kb_data = {
        "metadata": {
            "created_at": datetime.datetime.now().isoformat(),
            "source": os.path.basename(csv_path),
            "version": "1.0"
        }
    }
    
    # Baca file CSV
    try:
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            
            # Periksa header
            header = next(reader, None)
            has_header = header and len(header) >= 2 and "key" in header[0].lower()
            
            # Kembalikan ke awal file jika tidak ada header
            if not has_header:
                csvfile.seek(0)
            
            # Parse baris-baris
            for row in reader:
                if len(row) >= 2:  # Minimal ada key dan value
                    key = row[0].strip()
                    value = row[1].strip()
                    
                    # Category jika ada
                    category = row[2].strip() if len(row) > 2 else "general"
                    
                    # Tambahkan ke struktur KB
                    if category not in kb_data:
                        kb_data[category] = {}
                    
                    kb_data[category][key] = value
        
        # Simpan ke file
        with open(kb_path, 'w') as f:
            json.dump(kb_data, f, indent=4)
        
        return {
            "status": "success",
            "kb_path": kb_path,
            "categories": list(kb_data.keys()),
            "entries": sum(len(items) for cat, items in kb_data.items() if cat != "metadata")
        }
        
    except Exception as e:
        logger.error(f"Import CSV error: {str(e)}")
        return {"status": "error", "message": str(e)}

def merge_knowledge_bases(kb_names, output_name=None):
    """
    Menggabungkan beberapa knowledge base menjadi satu
    
    Args:
        kb_names (list): Daftar nama knowledge base
        output_name (str, optional): Nama kb output
        
    Returns:
        dict: Status merge
    """
    if not output_name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
        output_name = f"merged_{timestamp}"
    
    kb_dir = "data/knowledge_base"
    
    # Periksa apakah KB ada
    missing_kbs = []
    for kb_name in kb_names:
        kb_path = os.path.join(kb_dir, f"{kb_name}.json")
        if not os.path.exists(kb_path):
            missing_kbs.append(kb_name)
    
    if missing_kbs:
        return {"status": "error", "message": f"Knowledge bases not found: {', '.join(missing_kbs)}"}
    
    # Inisialisasi KB gabungan
    merged_kb = {
        "metadata": {
            "created_at": datetime.datetime.now().isoformat(),
            "source": f"Merged from: {', '.join(kb_names)}",
            "version": "1.0"
        }
    }
    
    # Gabungkan KB
    for kb_name in kb_names:
        kb_path = os.path.join(kb_dir, f"{kb_name}.json")
        
        try:
            with open(kb_path, 'r') as f:
                kb_data = json.load(f)
            
            # Tambahkan data (kecuali metadata)
            for category, items in kb_data.items():
                if category == "metadata":
                    continue
                
                if category not in merged_kb:
                    merged_kb[category] = {}
                
                # Tambahkan/update items
                for key, value in items.items():
                    merged_kb[category][key] = value
        
        except Exception as e:
            logger.error(f"Error reading {kb_name}: {str(e)}")
            return {"status": "error", "message": f"Error reading {kb_name}: {str(e)}"}
    
    # Simpan KB gabungan
    output_path = os.path.join(kb_dir, f"{output_name}.json")
    
    try:
        with open(output_path, 'w') as f:
            json.dump(merged_kb, f, indent=4)
        
        # Hitung stats
        categories = []
        total_entries = 0
        
        for category, items in merged_kb.items():
            if category != "metadata":
                categories.append(f"{category} ({len(items)})")
                total_entries += len(items)
        
        return {
            "status": "success",
            "kb_path": output_path,
            "kb_name": output_name,
            "categories": categories,
            "total_entries": total_entries
        }
    
    except Exception as e:
        logger.error(f"Error saving merged KB: {str(e)}")
        return {"status": "error", "message": f"Error saving merged KB: {str(e)}"}