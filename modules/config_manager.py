# modules/config_manager.py

"""
Modul untuk mengelola konfigurasi sistem
Menyediakan fungsi-fungsi untuk membaca dan menulis pengaturan
"""

import os
import json
import yaml
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data/logs/config.log", mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('config_manager')

# Default config
DEFAULT_CONFIG = {
    "app": {
        "name": "JTRADE AUTORESPONDER.AI",
        "version": "1.0.0",
        "environment": "development"
    },
    "telegram": {
        "api_timeout": 30,
        "connection_retries": 5
    },
    "ai": {
        "default_model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000,
        "retry_attempts": 3
    },
    "persona": {
        "default_style": "profesional",
        "response_delay": 1.5,
        "max_conversation_history": 10
    },
    "analytics": {
        "enable_tracking": True,
        "retention_days": 30
    },
    "storage": {
        "auto_backup": True,
        "backup_interval_days": 7,
        "cleanup_old_data": True,
        "data_retention_days": 90
    }
}

def get_config_path():
    """
    Dapatkan path file konfigurasi
    
    Returns:
        str: Path ke file konfigurasi
    """
    # Urutan pencarian konfigurasi
    config_paths = [
        "config/config.json",
        "config/config.yaml",
        "config.json"
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            return path
    
    # Jika tidak ditemukan, buat default
    os.makedirs("config", exist_ok=True)
    default_path = "config/config.json"
    
    with open(default_path, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    
    logger.info(f"Created default configuration at {default_path}")
    return default_path

def load_config():
    """
    Muat konfigurasi dari file
    
    Returns:
        dict: Konfigurasi sistem
    """
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()  # Start with defaults
    
    try:
        # Determine file type
        if config_path.endswith(".json"):
            with open(config_path, 'r') as f:
                file_config = json.load(f)
        elif config_path.endswith((".yaml", ".yml")):
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
        else:
            logger.warning(f"Unsupported config format: {config_path}")
            return config
        
        # Update config with values from file (deep merge)
        _deep_update(config, file_config)
        logger.info(f"Configuration loaded from {config_path}")
        
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
    
    return config

def _deep_update(target, source):
    """
    Deep update dictionary, similar to dict.update() but recursive
    
    Args:
        target (dict): Target dictionary to update
        source (dict): Source dictionary with new values
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value

def save_config(config, config_path=None):
    """
    Simpan konfigurasi ke file
    
    Args:
        config (dict): Konfigurasi yang akan disimpan
        config_path (str, optional): Path ke file konfigurasi
        
    Returns:
        bool: True jika berhasil, False jika gagal
    """
    if not config_path:
        config_path = get_config_path()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Write config based on file extension
        if config_path.endswith(".json"):
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        elif config_path.endswith((".yaml", ".yml")):
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        else:
            # Default to JSON
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
        
        logger.info(f"Configuration saved to {config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        return False

def update_config(updates, config_path=None):
    """
    Update konfigurasi dan simpan ke file
    
    Args:
        updates (dict): Perubahan yang akan diterapkan
        config_path (str, optional): Path ke file konfigurasi
        
    Returns:
        dict: Konfigurasi yang telah diperbarui
    """
    # Load current config
    config = load_config()
    
    # Apply updates (deep update)
    _deep_update(config, updates)
    
    # Save updated config
    save_config(config, config_path)
    
    return config

def get_specific_config(key_path, default=None):
    """
    Ambil nilai konfigurasi spesifik berdasarkan dot notation
    
    Args:
        key_path (str): Path ke konfigurasi (e.g., "ai.temperature")
        default: Nilai default jika konfigurasi tidak ditemukan
        
    Returns:
        object: Nilai konfigurasi atau default
    """
    config = load_config()
    keys = key_path.split('.')
    
    # Navigate through nested dict
    current = config
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default

def reset_config_to_default(config_path=None):
    """
    Reset konfigurasi ke nilai default
    
    Args:
        config_path (str, optional): Path ke file konfigurasi
        
    Returns:
        bool: True jika berhasil, False jika gagal
    """
    if not config_path:
        config_path = get_config_path()
    
    return save_config(DEFAULT_CONFIG, config_path)