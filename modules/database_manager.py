# modules/database_manager.py

"""
Modul untuk mengelola database JTRADE AUTORESPONDER.AI
Menyediakan fungsi-fungsi untuk interaksi dengan database
"""

import os
import sqlite3
import json
import datetime
import logging
from pathlib import Path
from contextlib import contextmanager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/logs/database.log", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('database_manager')

# Default database path
DEFAULT_DB_PATH = "data/db/jtrade.db"

class DatabaseManager:
    """
    Database Manager untuk JTRADE
    """
    
    def __init__(self, db_path=DEFAULT_DB_PATH):
        """
        Inisialisasi Database Manager
        
        Args:
            db_path (str): Path ke database SQLite
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """
        Inisialisasi skema database
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Buat tabel untuk mencatat performa model AI
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    user_id TEXT,
                    chat_id TEXT,
                    prompt_length INTEGER,
                    response_length INTEGER,
                    model TEXT,
                    temperature REAL,
                    max_tokens INTEGER,
                    tokens_used INTEGER,
                    response_time_ms INTEGER,
                    timestamp TIMESTAMP,
                    success BOOLEAN,
                    error_message TEXT
                )
                ''')
                
                # Buat tabel untuk penyimpanan cache (mengurangi API calls)
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS response_cache (
                    prompt_hash TEXT PRIMARY KEY,
                    prompt TEXT,
                    response TEXT,
                    model TEXT,
                    created_at TIMESTAMP,
                    last_used TIMESTAMP,
                    use_count INTEGER DEFAULT 1
                )
                ''')
                
                # Buat tabel untuk menyimpan feedback pengguna
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    chat_id TEXT,
                    message_id TEXT,
                    rating INTEGER,
                    feedback_text TEXT,
                    original_message TEXT,
                    original_response TEXT,
                    timestamp TIMESTAMP
                )
                ''')
                
                # Buat tabel untuk statistik harian
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    total_interactions INTEGER,
                    total_users INTEGER,
                    new_users INTEGER,
                    avg_response_time REAL,
                    success_rate REAL,
                    intent_distribution TEXT,
                    error_count INTEGER,
                    created_at TIMESTAMP
                )
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager untuk koneksi database
        
        Yields:
            sqlite3.Connection: Koneksi database
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def log_ai_performance(self, performance_data):
        """
        Log performa model AI
        
        Args:
            performance_data (dict): Data performa AI
            
        Returns:
            int: ID record atau None jika gagal
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get required fields
                username = performance_data.get('username', '')
                user_id = performance_data.get('user_id', '')
                chat_id = performance_data.get('chat_id', '')
                prompt_length = performance_data.get('prompt_length', 0)
                response_length = performance_data.get('response_length', 0)
                model = performance_data.get('model', 'unknown')
                temperature = performance_data.get('temperature', 0.7)
                max_tokens = performance_data.get('max_tokens', 0)
                tokens_used = performance_data.get('tokens_used', 0)
                response_time_ms = performance_data.get('response_time_ms', 0)
                timestamp = performance_data.get('timestamp', datetime.datetime.now().isoformat())
                success = performance_data.get('success', True)
                error_message = performance_data.get('error_message', '')
                
                cursor.execute('''
                INSERT INTO ai_performance (
                    username, user_id, chat_id, prompt_length, response_length, 
                    model, temperature, max_tokens, tokens_used, response_time_ms,
                    timestamp, success, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    username, user_id, chat_id, prompt_length, response_length,
                    model, temperature, max_tokens, tokens_used, response_time_ms,
                    timestamp, success, error_message
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error logging AI performance: {str(e)}")
            return None
    
    def get_cache_response(self, prompt_hash, max_age_hours=24):
        """
        Mendapatkan respons dari cache
        
        Args:
            prompt_hash (str): Hash dari prompt
            max_age_hours (int): Usia maksimum cache dalam jam
            
        Returns:
            str: Respons dari cache atau None jika tidak ditemukan
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate max age timestamp
                max_age = (datetime.datetime.now() - datetime.timedelta(hours=max_age_hours)).isoformat()
                
                cursor.execute('''
                SELECT response FROM response_cache
                WHERE prompt_hash = ? AND created_at > ?
                ''', (prompt_hash, max_age))
                
                result = cursor.fetchone()
                
                if result:
                    # Update last used and count
                    cursor.execute('''
                    UPDATE response_cache
                    SET last_used = ?, use_count = use_count + 1
                    WHERE prompt_hash = ?
                    ''', (datetime.datetime.now().isoformat(), prompt_hash))
                    conn.commit()
                    
                    return result[0]
                
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None
    
    def add_to_cache(self, prompt_hash, prompt, response, model):
        """
        Tambahkan respons ke cache
        
        Args:
            prompt_hash (str): Hash dari prompt
            prompt (str): Prompt asli
            response (str): Respons dari model
            model (str): Model AI yang digunakan
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                now = datetime.datetime.now().isoformat()
                
                cursor.execute('''
                INSERT OR REPLACE INTO response_cache (
                    prompt_hash, prompt, response, model, created_at, last_used, use_count
                ) VALUES (?, ?, ?, ?, ?, ?, 
                    CASE 
                        WHEN EXISTS (SELECT 1 FROM response_cache WHERE prompt_hash = ?) 
                        THEN (SELECT use_count + 1 FROM response_cache WHERE prompt_hash = ?)
                        ELSE 1
                    END
                )
                ''', (prompt_hash, prompt, response, model, now, now, prompt_hash, prompt_hash))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error adding to cache: {str(e)}")
            return False
    
    def record_user_feedback(self, feedback_data):
        """
        Rekam feedback pengguna
        
        Args:
            feedback_data (dict): Data feedback
            
        Returns:
            int: ID record atau None jika gagal
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get required fields
                user_id = feedback_data.get('user_id', '')
                chat_id = feedback_data.get('chat_id', '')
                message_id = feedback_data.get('message_id', '')
                rating = feedback_data.get('rating', 0)
                feedback_text = feedback_data.get('feedback_text', '')
                original_message = feedback_data.get('original_message', '')
                original_response = feedback_data.get('original_response', '')
                timestamp = feedback_data.get('timestamp', datetime.datetime.now().isoformat())
                
                cursor.execute('''
                INSERT INTO user_feedback (
                    user_id, chat_id, message_id, rating, feedback_text,
                    original_message, original_response, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, chat_id, message_id, rating, feedback_text,
                    original_message, original_response, timestamp
                ))
                
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error recording user feedback: {str(e)}")
            return None
    
    def update_daily_stats(self, date=None):
        """
        Update statistik harian
        
        Args:
            date (str, optional): Tanggal dalam format YYYY-MM-DD
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            if not date:
                date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate total interactions for the day
                cursor.execute('''
                SELECT COUNT(*) FROM ai_performance
                WHERE timestamp LIKE ?
                ''', (f"{date}%",))
                total_interactions = cursor.fetchone()[0]
                
                # Calculate total unique users
                cursor.execute('''
                SELECT COUNT(DISTINCT user_id) FROM ai_performance
                WHERE timestamp LIKE ?
                ''', (f"{date}%",))
                total_users = cursor.fetchone()[0]
                
                # Calculate new users (users with first interaction today)
                cursor.execute('''
                SELECT COUNT(*) FROM (
                    SELECT user_id, MIN(date(timestamp)) as first_date
                    FROM ai_performance
                    GROUP BY user_id
                    HAVING first_date = ?
                )
                ''', (date,))
                new_users = cursor.fetchone()[0]
                
                # Calculate average response time
                cursor.execute('''
                SELECT AVG(response_time_ms) FROM ai_performance
                WHERE timestamp LIKE ? AND success = 1
                ''', (f"{date}%",))
                avg_response_time = cursor.fetchone()[0] or 0
                
                # Calculate success rate
                cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*)
                FROM ai_performance
                WHERE timestamp LIKE ?
                ''', (f"{date}%",))
                success_rate = cursor.fetchone()[0] or 0
                
                # Count errors
                cursor.execute('''
                SELECT COUNT(*) FROM ai_performance
                WHERE timestamp LIKE ? AND success = 0
                ''', (f"{date}%",))
                error_count = cursor.fetchone()[0]
                
                # Insert or update daily stats
                cursor.execute('''
                INSERT OR REPLACE INTO daily_stats (
                    date, total_interactions, total_users, new_users,
                    avg_response_time, success_rate, error_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date, total_interactions, total_users, new_users,
                    avg_response_time, success_rate, error_count, 
                    datetime.datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating daily stats: {str(e)}")
            return False
    
    def get_performance_stats(self, days=7):
        """
        Dapatkan statistik performa
        
        Args:
            days (int): Jumlah hari yang akan dianalisis
            
        Returns:
            dict: Statistik performa
        """
        try:
            # Calculate start date
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get daily stats
                cursor.execute('''
                SELECT * FROM daily_stats
                WHERE date >= ?
                ORDER BY date
                ''', (start_date,))
                
                daily_results = [dict(row) for row in cursor.fetchall()]
                
                # Overall statistics
                cursor.execute('''
                SELECT 
                    COUNT(*) as total_interactions,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(response_time_ms) as avg_response_time,
                    COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*) as success_rate,
                    COUNT(CASE WHEN success = 0 THEN 1 END) as error_count
                FROM ai_performance
                WHERE date(timestamp) >= ?
                ''', (start_date,))
                
                overall = dict(cursor.fetchone())
                
                # Popular models
                cursor.execute('''
                SELECT model, COUNT(*) as count
                FROM ai_performance
                WHERE date(timestamp) >= ?
                GROUP BY model
                ORDER BY count DESC
                ''', (start_date,))
                
                models = [dict(row) for row in cursor.fetchall()]
                
                # User feedback summary
                cursor.execute('''
                SELECT 
                    AVG(rating) as avg_rating,
                    COUNT(*) as feedback_count,
                    COUNT(CASE WHEN rating >= 4 THEN 1 END) * 100.0 / COUNT(*) as positive_feedback_pct
                FROM user_feedback
                WHERE date(timestamp) >= ?
                ''', (start_date,))
                
                feedback = dict(cursor.fetchone())
                
                return {
                    "daily_stats": daily_results,
                    "overall_stats": overall,
                    "models_used": models,
                    "feedback_stats": feedback,
                    "period": {
                        "start_date": start_date,
                        "end_date": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "days": days
                    }
                }
                
        except Exception as e:
            logger.error(f"Error retrieving performance stats: {str(e)}")
            return {"error": str(e)}
    
    def clean_cache(self, max_age_days=7):
        """
        Bersihkan cache lama
        
        Args:
            max_age_days (int): Usia maksimum cache dalam hari
            
        Returns:
            int: Jumlah record yang dihapus
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Calculate max age timestamp
                max_age = (datetime.datetime.now() - datetime.timedelta(days=max_age_days)).isoformat()
                
                cursor.execute('''
                DELETE FROM response_cache
                WHERE last_used < ?
                ''', (max_age,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Cleaned {deleted_count} items from cache")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning cache: {str(e)}")
            return 0

# Initialize database manager
db_manager = DatabaseManager()

# Export functions for easy access
def log_ai_performance(performance_data):
    return db_manager.log_ai_performance(performance_data)

def get_cache_response(prompt_hash, max_age_hours=24):
    return db_manager.get_cache_response(prompt_hash, max_age_hours)

def add_to_cache(prompt_hash, prompt, response, model):
    return db_manager.add_to_cache(prompt_hash, prompt, response, model)

def record_user_feedback(feedback_data):
    return db_manager.record_user_feedback(feedback_data)

def update_daily_stats(date=None):
    return db_manager.update_daily_stats(date)

def get_performance_stats(days=7):
    return db_manager.get_performance_stats(days)

def clean_cache(max_age_days=7):
    return db_manager.clean_cache(max_age_days)