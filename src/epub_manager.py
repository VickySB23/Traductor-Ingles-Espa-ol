import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import warnings
import gc  # <--- IMPORTANTE: Garbage Collector

warnings.filterwarnings("ignore")

class EpubManager:
    def __init__(self, input_path):
        self.path = input_path
        # EbookLib carga todo en RAM. Para el futuro (Fase 3) podríamos implementar streaming real,
        # pero por ahora controlaremos la RAM limpiando objetos intermedios.
        self.book = epub.read_epub(input_path)

    def save(self, output_path):
        epub.write_epub(output_path, self.book)

    def process_text(self, batch_translator_func, logger=None):
        """
        Recorre el libro y aplica la función de traducción.
        """
        items = list(self.book.get_items())
        # Filtramos solo documentos de texto (XHTML)
        docs = [x for x in items if x.get_type() == ebooklib.ITEM_DOCUMENT]
        
        total_docs = len(docs)
        if logger: logger(f"📚 Libro cargado. {total_docs} capítulos detectados.")

        # Usamos un índice simple para no depender de tqdm en la GUI
        for i, item in enumerate(docs):
            try:
                # 1. Extraer contenido
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')

                # 2. Buscar etiquetas traducibles
                tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li', 'div', 'span', 'caption'])
                valid_tags = [t for t in tags if t.string and t.string.strip()]

                if valid_tags:
                    if logger: logger(f"📝 Traduciendo cap {i+1}/{total_docs} ({len(valid_tags)} frases)...")
                    
                    # Extraer texto
                    raw_texts = [t.string for t in valid_tags]

                    # Traducir (Llamada al Engine)
                    translated_texts = batch_translator_func(raw_texts)
                    
                    # Reemplazar en HTML
                    for tag, trans in zip(valid_tags, translated_texts):
                        # replace_with mantiene la etiqueta <p> pero cambia el contenido
                        tag.string.replace_with(trans)
                    
                    # Guardar cambios en el objeto libro
                    item.set_content(soup.prettify("utf-8"))

                # --- ZONA CRÍTICA DE MEMORIA ---
                # Liberamos variables pesadas manualmente
                del soup
                del content
                del valid_tags
                # Forzamos limpieza de RAM
                gc.collect() 
                # -------------------------------

            except Exception as e:
                if logger: logger(f"⚠️ Error en capítulo {item.get_name()}: {e}", "red")

        if logger: logger("✨ Procesamiento de texto finalizado.")