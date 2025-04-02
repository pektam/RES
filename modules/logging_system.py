# modules/logging_system.py

"""
Modul untuk sistem logging JTRADE AUTORESPONDER.AI
Menyediakan fungsi logging terpusat dan sistem notifikasi
"""

import os
import sys
import json
import logging
import datetime
import traceback
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log directories
LOGS_DIR = "data/logs"
ERROR_LOGS_DIR = os.path.join(LOGS_DIR, "errors")
API_LOGS_DIR = os.path.join(LOGS_DIR, "api")
CONVERSATION_LOGS_DIR = os.path.join(LOGS_DIR, "conversations")

# Ensure directories exist
for dir_path in [LOGS_DIR, ERROR_LOGS_DIR, API_LOGS_DIR, CONVERSATION_LOGS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

class JTradeLogger:
    """
    Class untuk mengelola logging terpusat
    """
    
    def __init__(self, name, log_level=None):
        """
        Inisialisasi logger
        
        Args:
            name (str): Nama logger (biasanya nama modul)
            log_level (int, optional): Level log (logging.DEBUG, logging.INFO, dll)
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Set level
        self.logger.setLevel(log_level or DEFAULT_LOG_LEVEL)
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """
        Setup handlers untuk logger
        """
        # Create log file path
        log_file = os.path.join(LOGS_DIR, f"{self.name}.log")
        
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=10
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Create error log handler (only ERROR and above)
        error_log_file = os.path.join(ERROR_LOGS_DIR, f"{self.name}_error.log")
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def debug(self, message, *args, **kwargs):
        """Log DEBUG level message"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """Log INFO level message"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """Log WARNING level message"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """Log ERROR level message"""
        exc_info = kwargs.pop('exc_info', sys.exc_info())
        self.logger.error(message, exc_info=exc_info, *args, **kwargs)
        
        # Log error details to special file
        if exc_info and exc_info[0]:
            self._log_exception_details(message, exc_info)
    
    def critical(self, message, *args, **kwargs):
        """Log CRITICAL level message"""
        exc_info = kwargs.pop('exc_info', sys.exc_info())
        self.logger.critical(message, exc_info=exc_info, *args, **kwargs)
        
        # Log critical details to special file
        if exc_info and exc_info[0]:
            self._log_exception_details(message, exc_info, level="CRITICAL")
    
    def _log_exception_details(self, message, exc_info, level="ERROR"):
        """
        Log detailed exception info to a structured file
        """
        timestamp = datetime.datetime.now().isoformat()
        error_file = os.path.join(
            ERROR_LOGS_DIR, 
            f"exception_{timestamp.replace(':', '-')}.json"
        )
        
        error_data = {
            "timestamp": timestamp,
            "logger": self.name,
            "level": level,
            "message": message,
            "exception_type": exc_info[0].__name__ if exc_info[0] else None,
            "exception_message": str(exc_info[1]) if exc_info[1] else None,
            "traceback": traceback.format_exception(*exc_info) if exc_info[0] else None
        }
        
        with open(error_file, 'w') as f:
            json.dump(error_data, f, indent=4)
    
    def log_api_call(self, endpoint, request_data, response_data, response_time, status_code):
        """
        Log API call details
        
        Args:
            endpoint (str): API endpoint
            request_data (dict): Request data
            response_data (dict): Response data
            response_time (float): Response time in seconds
            status_code (int): HTTP status code
        """
        timestamp = datetime.datetime.now().isoformat()
        log_file = os.path.join(
            API_LOGS_DIR, 
            f"api_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        )
        
        log_data = {
            "timestamp": timestamp,
            "endpoint": endpoint,
            "request": request_data,
            "response": response_data,
            "response_time_ms": round(response_time * 1000, 2),
            "status_code": status_code
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_data) + "\n")
    
    def log_conversation(self, username, chat_id, user_id, user_message, bot_response):
        """
        Log conversation details
        
        Args:
            username (str): Username akun JTRADE
            chat_id (str/int): Chat ID
            user_id (str/int): User ID
            user_message (str): Pesan dari pengguna
            bot_response (str): Respons dari bot
        """
        timestamp = datetime.datetime.now().isoformat()
        log_file = os.path.join(
            CONVERSATION_LOGS_DIR, 
            f"conv_{username}_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
        )
        
        log_data = {
            "timestamp": timestamp,
            "username": username,
            "chat_id": chat_id,
            "user_id": user_id,
            "user_message": user_message,
            "bot_response": bot_response
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_data) + "\n")

def get_logger(name, log_level=None):
    """
    Dapatkan instance JTradeLogger
    
    Args:
        name (str): Nama logger
        log_level (int, optional): Level log
        
    Returns:
        JTradeLogger: Instance logger
    """
    return JTradeLogger(name, log_level)

def setup_global_exception_handler():
    """
    Setup global exception handler
    """
    def handle_exception(exc_type, exc_value, exc_traceback):
        # Ignore KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log the exception
        logger = get_logger("global")
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Set the excepthook
    sys.excepthook = handle_exception

def get_error_logs(days=7, level=None):
    """
    Dapatkan daftar log error
    
    Args:
        days (int): Jumlah hari yang akan diperiksa
        level (str, optional): Filter berdasarkan level (ERROR, CRITICAL)
        
    Returns:
        list: Daftar log error
    """
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    error_logs = []
    
    # Get all JSON error files
    for file_path in Path(ERROR_LOGS_DIR).glob("exception_*.json"):
        # Check file modification time
        if datetime.datetime.fromtimestamp(file_path.stat().st_mtime) >= cutoff_date:
            try:
                with open(file_path, 'r') as f:
                    log_data = json.load(f)
                
                # Filter by level if specified
                if level and log_data.get('level') != level:
                    continue
                
                error_logs.append(log_data)
            except Exception as e:
                print(f"Error reading {file_path}: {str(e)}")
    
    # Sort by timestamp (newest first)
    error_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return error_logs

def clear_old_logs(days=30):
    """
    Bersihkan log lama
    
    Args:
        days (int): Hapus log yang lebih lama dari ini
        
    Returns:
        int: Jumlah file yang dihapus
    """
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    deleted_count = 0
    
    # Directories to check
    log_dirs = [LOGS_DIR, ERROR_LOGS_DIR, API_LOGS_DIR, CONVERSATION_LOGS_DIR]
    
    for dir_path in log_dirs:
        for file_path in Path(dir_path).glob("*.*"):
            # Skip directories
            if file_path.is_dir():
                continue
            
            # Check file modification time
            if datetime.datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff_date:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {file_path}: {str(e)}")
    
    return deleted_count