import os

# Rutas Base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# Configuración IA
DEFAULT_MODEL = "Helsinki-NLP/opus-mt-en-es"
BATCH_SIZE = 8  # Aumentar si tienes buena VRAM (16, 32)
MAX_LENGTH = 512

# Configuración DB
DB_PATH = os.path.join(CACHE_DIR, "translation_memory.db")