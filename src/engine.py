import torch
from transformers import MarianMTModel, MarianTokenizer
from .config import DEFAULT_MODEL, MAX_LENGTH

class AI_Engine:
    def __init__(self, model_name=DEFAULT_MODEL, use_gpu=True, tm=None):
        self.tm = tm  # Instancia de TranslationMemory
        
        # 1. Detectar hardware real
        if use_gpu and torch.cuda.is_available():
            self.device = "cuda"
            print("🚀 ACELERACIÓN GPU: ACTIVADA")
        else:
            self.device = "cpu"
            print("🐢 MODO CPU: ACTIVADO")

        # 2. Cargar Tokenizer
        self.tokenizer = MarianTokenizer.from_pretrained(model_name)
        
        # 3. Cargar Modelo con Optimización
        print(f"⚡ Cargando modelo en RAM...")
        self.model = MarianMTModel.from_pretrained(model_name)

        if self.device == "cpu":
            # TRUCO PRO: Cuantización Dinámica (Hace que vaya 2x más rápido en CPU)
            print("🔧 Optimizando tensores para CPU (Cuantización 8-bit)...")
            self.model = torch.quantization.quantize_dynamic(
                self.model, {torch.nn.Linear}, dtype=torch.qint8
            )

        self.model.to(self.device)

    def translate_batch(self, texts):
        results = [None] * len(texts)
        indices_to_translate = []
        texts_to_translate = []

        # A. Revisar Memoria de Traducción (Cache) primero
        for i, text in enumerate(texts):
            clean_text = text.strip()
            if not clean_text:
                results[i] = text
                continue
            
            # Si tenemos TM y encontramos la frase, nos ahorramos la IA
            if self.tm:
                cached = self.tm.get(clean_text)
                if cached:
                    results[i] = cached
                    continue
            
            indices_to_translate.append(i)
            texts_to_translate.append(clean_text)

        # B. Traducir lo que falta con la IA
        if texts_to_translate:
            try:
                inputs = self.tokenizer(
                    texts_to_translate, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True, 
                    max_length=MAX_LENGTH
                ).to(self.device)

                with torch.no_grad():
                    generated = self.model.generate(**inputs)
                
                translated_texts = self.tokenizer.batch_decode(generated, skip_special_tokens=True)

                # Guardar resultados y actualizar Cache
                for idx_list, translation in enumerate(translated_texts):
                    original_index = indices_to_translate[idx_list]
                    original_text = texts_to_translate[idx_list]
                    
                    results[original_index] = translation
                    
                    if self.tm:
                        self.tm.save(original_text, translation)
            except Exception as e:
                print(f"Error en batch: {e}")
                # En caso de error, devolvemos el original para no romper el libro
                for idx in indices_to_translate:
                    results[idx] = texts[idx]

        return results