import sqlite3
from .config import DB_PATH
from .utils import calculate_hash

class TranslationMemory:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        # source_hash es la clave primaria para búsquedas O(1)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                source_hash TEXT PRIMARY KEY,
                source_text TEXT,
                target_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def get(self, text):
        """Retorna la traducción si existe, o None"""
        if not text: return None
        text_hash = calculate_hash(text)
        self.cursor.execute("SELECT target_text FROM translations WHERE source_hash=?", (text_hash,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def save(self, original, translated):
        """Guarda una nueva traducción"""
        if not original or not translated: return
        text_hash = calculate_hash(original)
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO translations (source_hash, source_text, target_text) VALUES (?, ?, ?)",
                (text_hash, original, translated)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error DB: {e}")

    def close(self):
        self.conn.close()