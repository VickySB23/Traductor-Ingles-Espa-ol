import hashlib
import logging
import os
from datetime import datetime
from .config import LOGS_DIR

def setup_logger():
    """Configura un logger que escribe en archivo y consola"""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    filename = datetime.now().strftime("run_%Y-%m-%d.log")
    log_path = os.path.join(LOGS_DIR, filename)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("TraductorPro")

def calculate_hash(text):
    """Genera un hash SHA256 único para un texto"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def get_file_hash(filepath):
    """Calcula el hash de un archivo para verificar cambios"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()