import json
import os
import re

class GlossaryManager:
    def __init__(self, glossary_path="data/glossary.json"):
        self.rules = {}
        # Buscamos el archivo subiendo un nivel desde src/ para encontrar data/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.join(base_dir, glossary_path)

        if os.path.exists(abs_path):
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
                print(f"📚 Glosario cargado: {len(self.rules)} reglas activas.")
            except Exception as e:
                print(f"⚠️ Error leyendo glossary.json: {e}")
        else:
            print(f"ℹ️ No se encontró glosario en {abs_path}. Se usará traducción estándar.")

    def apply_post_correction(self, text):
        """
        Reemplaza palabras clave DESPUÉS de la traducción.
        """
        if not text: return text
        
        for original, correccion in self.rules.items():
            # Usamos expresiones regulares para reemplazar solo palabras completas
            # (Evita que 'pan' reemplace partes de 'panda')
            pattern = re.compile(re.escape(original), re.IGNORECASE)
            text = pattern.sub(correccion, text)
            
        return text