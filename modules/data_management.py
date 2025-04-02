# modules/data_management.py

"""
Modul untuk manajemen data JTRADE AUTORESPONDER.AI
Membantu mengelola, membersihkan, dan mentransformasi data
"""

import os
import json
import shutil
import datetime
import zipfile
import csv
from pathlib import Path

def list_conversations(username=None, limit=None, sort_by="latest"):
    """
    List semua riwayat percakapan
    
    Args:
        username (str, optional): Filter by username
        limit (int, optional): Batasi jumlah hasil
        sort_by (str): Kriteria pengurutan ('latest', 'oldest', 'size')
        
    Returns:
        list: Daftar file percakapan
    """
    conv_dir = "data/conversations"
    if not os.path.exists(conv_dir):
        return []
    
    # Ambil semua file percakapan
    files = []
    pattern = f"{username}_*" if username else "*"
    
    for filepath in Path(conv_dir).glob(pattern):
        if filepath.is_file() and filepath.suffix.lower() == '.json':
            file_info = {
                "path": str(filepath),
                "filename": filepath.name,
                "size": filepath.stat().st_size,
                "modified": datetime.datetime.fromtimestamp(filepath.stat().st_mtime)
            }
            
            # Parse username dan ID
            parts = filepath.stem.split('_')
            if len(parts) >= 3:
                file_info["username"] = parts[0]
                file_info["chat_id"] = parts[1]
                file_info["user_id"] = parts[2]
            
            # Load a bit of content to get metadata
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if data:
                    if isinstance(data, list) and len(data) > 0:
                        file_info["messages"] = len(data)
                        file_info["first_timestamp"] = data[0].get("timestamp", "")
                        file_info["last_timestamp"] = data[-1].get("timestamp", "")
            except Exception as e:
                file_info["error"] = str(e)
            
            files.append(file_info)
    
    # Sort files
    if sort_by == "latest":
        files.sort(key=lambda x: x.get("modified", datetime.datetime.min), reverse=True)
    elif sort_by == "oldest":
        files.sort(key=lambda x: x.get("modified", datetime.datetime.min))
    elif sort_by == "size":
        files.sort(key=lambda x: x.get("size", 0), reverse=True)
    
    # Apply limit if specified
    if limit and isinstance(limit, int) and limit > 0:
        files = files[:limit]
    
    return files

def get_conversation_data(username, chat_id, user_id):
    """
    Mendapatkan data percakapan lengkap
    
    Args:
        username (str): Username akun JTRADE
        chat_id (str/int): ID chat
        user_id (str/int): ID pengguna
        
    Returns:
        dict: Data percakapan dengan metadata
    """
    filename = f"data/conversations/{username}_{chat_id}_{user_id}.json"
    
    if not os.path.exists(filename):
        return {"error": "File not found"}
    
    try:
        with open(filename, 'r') as f:
            raw_data = json.load(f)
        
        # Extract metadata
        metadata = {
            "username": username,
            "chat_id": chat_id,
            "user_id": user_id,
            "filepath": filename,
            "message_count": len(raw_data),
            "filesize": os.path.getsize(filename),
            "last_modified": datetime.datetime.fromtimestamp(os.path.getmtime(filename)).isoformat()
        }
        
        # Count message types
        incoming = [msg for msg in raw_data if msg.get("type") == "incoming"]
        outgoing = [msg for msg in raw_data if msg.get("type") == "outgoing"]
        
        metadata["incoming_count"] = len(incoming)
        metadata["outgoing_count"] = len(outgoing)
        
        # Get time range
        if raw_data:
            try:
                first_timestamp = raw_data[0].get("timestamp", "")
                last_timestamp = raw_data[-1].get("timestamp", "")
                
                # Calculate duration if possible
                if first_timestamp and last_timestamp:
                    first_dt = datetime.datetime.fromisoformat(first_timestamp)
                    last_dt = datetime.datetime.fromisoformat(last_timestamp)
                    duration = last_dt - first_dt
                    metadata["duration_seconds"] = duration.total_seconds()
                    metadata["duration_formatted"] = str(duration)
            except Exception as e:
                metadata["timestamp_error"] = str(e)
        
        return {
            "metadata": metadata,
            "messages": raw_data
        }
        
    except Exception as e:
        return {"error": str(e)}

def backup_data(target_dir=None, include_analytics=True, include_conversations=True, include_kb=True):
    """
    Buat backup data ke direktori atau file ZIP
    
    Args:
        target_dir (str, optional): Direktori tujuan backup. Jika None, buat di data/backups/
        include_analytics (bool): Sertakan data analitik
        include_conversations (bool): Sertakan data percakapan
        include_kb (bool): Sertakan knowledge base
        
    Returns:
        str: Path ke file/folder backup
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Buat direktori backup jika tidak ada
    if not target_dir:
        target_dir = f"data/backups/backup_{timestamp}"
        
    # Pastikan direktori ada
    os.makedirs(target_dir, exist_ok=True)
    
    # Daftar direktori yang akan dibackup
    to_backup = []
    if include_analytics and os.path.exists("data/analytics"):
        to_backup.append("data/analytics")
    
    if include_conversations and os.path.exists("data/conversations"):
        to_backup.append("data/conversations")
    
    if include_kb and os.path.exists("data/knowledge_base"):
        to_backup.append("data/knowledge_base")
    
    # Tambahkan file log jika ada
    if os.path.exists("data/logs"):
        to_backup.append("data/logs")
    
    # Lakukan backup
    backup_info = {
        "timestamp": timestamp,
        "backup_path": target_dir,
        "included_directories": to_backup,
        "files_copied": {}
    }
    
    for src_dir in to_backup:
        # Get the destination directory (preserve the structure)
        rel_path = os.path.relpath(src_dir, "data")
        dst_dir = os.path.join(target_dir, rel_path)
        
        # Create the destination directory
        os.makedirs(dst_dir, exist_ok=True)
        
        # Copy files
        file_count = 0
        for src_file in Path(src_dir).glob("**/*"):
            if src_file.is_file():
                # Calculate destination path
                rel_file_path = src_file.relative_to(src_dir)
                dst_file = os.path.join(dst_dir, str(rel_file_path))
                
                # Ensure parent directory exists
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                
                # Copy file
                shutil.copy2(src_file, dst_file)
                file_count += 1
        
        backup_info["files_copied"][src_dir] = file_count
    
    # Write backup info
    with open(os.path.join(target_dir, "backup_info.json"), 'w') as f:
        json.dump(backup_info, f, indent=4)
    
    return target_dir

def create_zip_backup(output_path=None):
    """
    Buat backup dalam bentuk file ZIP
    
    Args:
        output_path (str, optional): Path untuk file ZIP output. Jika None, buat di data/backups/
        
    Returns:
        str: Path ke file ZIP
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Buat direktori temporary untuk backup
    temp_dir = f"data/backups/temp_{timestamp}"
    
    # Backup ke direktori temporary
    backup_data(target_dir=temp_dir)
    
    # Tentukan nama file ZIP
    if not output_path:
        # Pastikan direktori backups ada
        os.makedirs("data/backups", exist_ok=True)
        output_path = f"data/backups/backup_{timestamp}.zip"
    
    # Buat file ZIP
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Hitung path relatif untuk arsip
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    # Hapus direktori temporary
    shutil.rmtree(temp_dir)
    
    return output_path

def export_conversations_to_csv(username=None, output_path=None):
    """
    Export riwayat percakapan ke file CSV
    
    Args:
        username (str, optional): Username untuk filter data
        output_path (str, optional): Path untuk file CSV output
        
    Returns:
        str: Path ke file CSV
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Tentukan nama file output
    if not output_path:
        os.makedirs("data/export", exist_ok=True)
        if username:
            output_path = f"data/export/{username}_conversations_{timestamp}.csv"
        else:
            output_path = f"data/export/all_conversations_{timestamp}.csv"
    
    # Ambil daftar file percakapan
    conv_files = list_conversations(username=username)
    
    if not conv_files:
        return "No conversations found"
    
    # Buat file CSV
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(['Username', 'Chat ID', 'User ID', 'Timestamp', 'Type', 'Content'])
        
        # Process each file
        for file_info in conv_files:
            try:
                filepath = file_info["path"]
                username = file_info.get("username", "unknown")
                chat_id = file_info.get("chat_id", "unknown")
                user_id = file_info.get("user_id", "unknown")
                
                with open(filepath, 'r') as f:
                    messages = json.load(f)
                
                for message in messages:
                    writer.writerow([
                        username,
                        chat_id,
                        user_id,
                        message.get("timestamp", ""),
                        message.get("type", ""),
                        message.get("content", "")
                    ])
            except Exception as e:
                # Write error record
                writer.writerow([
                    file_info.get("username", "unknown"),
                    file_info.get("chat_id", "unknown"),
                    file_info.get("user_id", "unknown"),
                    "",
                    "ERROR",
                    f"Error processing file: {str(e)}"
                ])
    
    return output_path

def cleanup_old_data(days_threshold=30, data_types=None):
    """
    Membersihkan data lama
    
    Args:
        days_threshold (int): Berapa hari untuk menyimpan data
        data_types (list): Tipe data yang akan dibersihkan ('analytics', 'conversations', 'visualizations')
        
    Returns:
        dict: Informasi jumlah file yang dihapus
    """
    if not data_types:
        data_types = ['analytics', 'visualizations']  # Default, don't include conversations
    
    # Konversi threshold ke datetime
    threshold_date = datetime.datetime.now() - datetime.timedelta(days=days_threshold)
    
    # Direktori untuk setiap tipe data
    dir_map = {
        'analytics': 'data/analytics',
        'conversations': 'data/conversations',
        'visualizations': 'data/visualizations',
        'exports': 'data/export',
        'reports': 'data/reports'
    }
    
    results = {}
    
    # Proses setiap tipe data
    for data_type in data_types:
        if data_type not in dir_map:
            continue
            
        directory = dir_map[data_type]
        if not os.path.exists(directory):
            results[data_type] = {"error": "Directory not found"}
            continue
        
        # Hitung file yang harus dihapus
        to_delete = []
        
        for file_path in Path(directory).glob("*"):
            if file_path.is_file():
                # Cek tanggal modifikasi
                mod_time = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                if mod_time < threshold_date:
                    to_delete.append(file_path)
        
        # Buat direktori arsip (untuk file lama)
        if to_delete:
            archive_dir = f"{directory}/archive"
            os.makedirs(archive_dir, exist_ok=True)
            
            # Arsipkan file lama (tidak langsung hapus)
            for file_path in to_delete:
                # Pindahkan ke arsip
                dest_path = os.path.join(archive_dir, file_path.name)
                shutil.move(str(file_path), dest_path)
        
        results[data_type] = {"files_archived": len(to_delete)}
    
    return results
