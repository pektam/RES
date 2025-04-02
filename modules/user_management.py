# modules/user_management.py

"""
Modul untuk mengelola data pengguna
Menyediakan fungsi-fungsi untuk tracking dan analisis pengguna
"""

import os
import json
import datetime
import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/logs/users.log", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('user_management')

class UserManager:
    def __init__(self, db_path="data/db/jtrade.db"):
        """
        Inisialisasi User Manager
        
        Args:
            db_path (str): Path ke database SQLite
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """
        Inisialisasi database jika belum ada
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                chat_id TEXT,
                telegram_username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone_number TEXT,
                language_code TEXT,
                registration_date TIMESTAMP,
                last_active TIMESTAMP,
                status TEXT,
                metadata TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id TEXT,
                preference_key TEXT,
                preference_value TEXT,
                updated_at TIMESTAMP,
                PRIMARY KEY (user_id, preference_key),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_segments (
                segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                segment_name TEXT UNIQUE,
                segment_description TEXT,
                creation_date TIMESTAMP,
                criteria TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_segment_members (
                segment_id INTEGER,
                user_id TEXT,
                added_at TIMESTAMP,
                PRIMARY KEY (segment_id, user_id),
                FOREIGN KEY (segment_id) REFERENCES user_segments(segment_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
    
    def register_user(self, user_data):
        """
        Mendaftarkan pengguna baru atau memperbarui yang sudah ada
        
        Args:
            user_data (dict): Data pengguna dari Telegram
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            user_id = str(user_data.get('id', ''))
            if not user_id:
                logger.error("Invalid user data: missing id")
                return False
            
            # Prepare data
            now = datetime.datetime.now().isoformat()
            chat_id = user_data.get('chat_id', '')
            username = user_data.get('username', '')
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            phone = user_data.get('phone', '')
            lang_code = user_data.get('language_code', 'id')
            
            # Additional metadata as JSON
            metadata = {k: v for k, v in user_data.items() 
                      if k not in ['id', 'chat_id', 'username', 'first_name', 
                                  'last_name', 'phone', 'language_code']}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            user_exists = cursor.fetchone()
            
            if user_exists:
                # Update existing user
                cursor.execute('''
                UPDATE users SET 
                    chat_id = COALESCE(?, chat_id),
                    telegram_username = COALESCE(?, telegram_username),
                    first_name = COALESCE(?, first_name),
                    last_name = COALESCE(?, last_name),
                    phone_number = COALESCE(?, phone_number),
                    language_code = COALESCE(?, language_code),
                    last_active = ?,
                    metadata = CASE 
                        WHEN ? != '{}' THEN ?
                        ELSE metadata
                    END
                WHERE user_id = ?
                ''', (
                    chat_id or None, 
                    username or None, 
                    first_name or None, 
                    last_name or None,
                    phone or None,
                    lang_code or None,
                    now,
                    json.dumps(metadata),
                    json.dumps(metadata),
                    user_id
                ))
                
                logger.info(f"Updated user: {user_id} ({username})")
            else:
                # Insert new user
                cursor.execute('''
                INSERT INTO users (
                    user_id, chat_id, telegram_username, first_name, last_name,
                    phone_number, language_code, registration_date, last_active,
                    status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, chat_id, username, first_name, last_name,
                    phone, lang_code, now, now, 'active', json.dumps(metadata)
                ))
                
                logger.info(f"Registered new user: {user_id} ({username})")
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return False
    
    def get_user(self, user_id):
        """
        Mendapatkan data pengguna berdasarkan ID
        
        Args:
            user_id (str): ID pengguna
            
        Returns:
            dict: Data pengguna atau None jika tidak ditemukan
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to dict
            user_data = dict(row)
            
            # Parse metadata JSON
            try:
                metadata = json.loads(user_data.get('metadata', '{}'))
                user_data['metadata'] = metadata
            except:
                user_data['metadata'] = {}
            
            # Get preferences
            cursor.execute(
                "SELECT preference_key, preference_value FROM user_preferences WHERE user_id = ?", 
                (user_id,)
            )
            preferences = {row[0]: row[1] for row in cursor.fetchall()}
            user_data['preferences'] = preferences
            
            conn.close()
            return user_data
            
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {str(e)}")
            return None
    
    def update_user_activity(self, user_id):
        """
        Update timestamp aktivitas terakhir pengguna
        
        Args:
            user_id (str): ID pengguna
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            now = datetime.datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET last_active = ? WHERE user_id = ?", 
                (now, user_id)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating user activity for {user_id}: {str(e)}")
            return False
    
    def set_user_preference(self, user_id, key, value):
        """
        Set preferensi pengguna
        
        Args:
            user_id (str): ID pengguna
            key (str): Kunci preferensi
            value (str): Nilai preferensi
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            now = datetime.datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # First check if user exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                logger.warning(f"Cannot set preference - user {user_id} not found")
                return False
            
            # Upsert preference
            cursor.execute('''
            INSERT INTO user_preferences (user_id, preference_key, preference_value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (user_id, preference_key) 
            DO UPDATE SET preference_value = ?, updated_at = ?
            ''', (user_id, key, value, now, value, now))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error setting preference for {user_id}: {str(e)}")
            return False
    
    def get_user_preference(self, user_id, key, default=None):
        """
        Mendapatkan preferensi pengguna
        
        Args:
            user_id (str): ID pengguna
            key (str): Kunci preferensi
            default: Nilai default jika preferensi tidak ditemukan
            
        Returns:
            str/object: Nilai preferensi atau default
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT preference_value FROM user_preferences WHERE user_id = ? AND preference_key = ?", 
                (user_id, key)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else default
            
        except Exception as e:
            logger.error(f"Error getting preference for {user_id}: {str(e)}")
            return default
    
    def create_segment(self, name, description, criteria=None):
        """
        Membuat segment pengguna baru
        
        Args:
            name (str): Nama segment
            description (str): Deskripsi segment
            criteria (dict, optional): Kriteria untuk segment
            
        Returns:
            int: ID segment baru atau None jika gagal
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.datetime.now().isoformat()
            criteria_json = json.dumps(criteria) if criteria else '{}'
            
            cursor.execute('''
            INSERT INTO user_segments (segment_name, segment_description, creation_date, criteria)
            VALUES (?, ?, ?, ?)
            ''', (name, description, now, criteria_json))
            
            segment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created segment: {name} (ID: {segment_id})")
            return segment_id
            
        except Exception as e:
            logger.error(f"Error creating segment: {str(e)}")
            return None
    
    def add_user_to_segment(self, user_id, segment_id):
        """
        Tambahkan pengguna ke segment
        
        Args:
            user_id (str): ID pengguna
            segment_id (int): ID segment
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            now = datetime.datetime.now().isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if segment exists
            cursor.execute("SELECT segment_id FROM user_segments WHERE segment_id = ?", (segment_id,))
            if not cursor.fetchone():
                logger.warning(f"Segment {segment_id} not found")
                return False
            
            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                logger.warning(f"User {user_id} not found")
                return False
            
            # Add user to segment
            cursor.execute('''
            INSERT OR REPLACE INTO user_segment_members (segment_id, user_id, added_at)
            VALUES (?, ?, ?)
            ''', (segment_id, user_id, now))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error adding user to segment: {str(e)}")
            return False
    
    def get_segment_users(self, segment_id, limit=None):
        """
        Mendapatkan daftar pengguna dalam segment
        
        Args:
            segment_id (int): ID segment
            limit (int, optional): Batasi jumlah hasil
            
        Returns:
            list: Daftar pengguna dalam segment
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
            SELECT u.* FROM users u
            JOIN user_segment_members m ON u.user_id = m.user_id
            WHERE m.segment_id = ?
            ORDER BY u.last_active DESC
            '''
            
            if limit:
                query += f" LIMIT {int(limit)}"
            
            cursor.execute(query, (segment_id,))
            users = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return users
            
        except Exception as e:
            logger.error(f"Error getting users for segment {segment_id}: {str(e)}")
            return []
    
    def get_active_users(self, days=7):
        """
        Mendapatkan daftar pengguna aktif dalam periode tertentu
        
        Args:
            days (int): Periode dalam hari
            
        Returns:
            list: Daftar pengguna aktif
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate the cutoff date
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            cursor.execute('''
            SELECT * FROM users
            WHERE last_active >= ?
            ORDER BY last_active DESC
            ''', (cutoff,))
            
            active_users = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return active_users
            
        except Exception as e:
            logger.error(f"Error getting active users: {str(e)}")
            return []
    
    def get_user_stats(self):
        """
        Mendapatkan statistik pengguna
        
        Returns:
            dict: Statistik pengguna
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            # Active today
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE last_active LIKE ?", 
                (f"{today}%",)
            )
            active_today = cursor.fetchone()[0]
            
            # Active this week
            week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE last_active >= ?", 
                (week_ago,)
            )
            active_this_week = cursor.fetchone()[0]
            
            # New this week
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE registration_date >= ?", 
                (week_ago,)
            )
            new_this_week = cursor.fetchone()[0]
            
            # Users by language
            cursor.execute('''
            SELECT language_code, COUNT(*) as count 
            FROM users 
            GROUP BY language_code
            ORDER BY count DESC
            ''')
            languages = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                "total_users": total_users,
                "active_today": active_today,
                "active_this_week": active_this_week,
                "new_this_week": new_this_week,
                "users_by_language": languages,
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        except Exception as e:
    logger.error(f"Error getting user stats: {str(e)}")
    return {
        "error": str(e),
        "timestamp": datetime.datetime.now().isoformat()
    }