import torch
from transformers import MarianMTModel, MarianTokenizer
from .config import DEFAULT_MODEL, MAX_LENGTH
from .glossary import GlossaryManager  # <--- NUEVO IMPORT

class AI_Engine:
    def __init__(self, model_name=DEFAULT_MODEL, use_gpu=True, tm=None):
        self.tm = tm
        self.glossary = GlossaryManager()  # <--- INICIALIZAMOS EL GLOSARIO
        
        # 1. Detectar hardware
        if use_gpu and torch.cuda.is_available():
            self.device = "cuda"
            print("🚀 ACELERACIÓN GPU: ACTIVADA")
        else:
            self.device = "cpu"
            print("🐢 MODO CPU: ACTIVADO")

        # 2. Cargar Tokenizer y Modelo
        self.tokenizer = MarianTokenizer.from_pretrained(model_name)
        print(f"⚡ Cargando modelo en RAM...")
        self.model = MarianMTModel.from_pretrained(model_name)

        # 3. Optimización para CPU (Si aplica)
        if self.device == "cpu":
            print("🔧 Optimizando tensores para CPU (Cuantización 8-bit)...")
            self.model = torch.quantization.quantize_dynamic(
                self.model, {torch.nn.Linear}, dtype=torch.qint8
            )

        self.model.to(self.device)

    def translate_batch(self, texts):
        results = [None] * len(texts)
        indices_to_translate = []
        texts_to_translate = []

        # A. Revisar Cache (Memoria de Traducción)
        for i, text in enumerate(texts):
            clean_text = text.strip()
            if not clean_text:
                results[i] = text
                continue
            
            if self.tm:
                cached = self.tm.get(clean_text)
                if cached:
                    # IMPORTANTE: Aplicamos glosario incluso a lo que viene del caché
                    # por si cambiaste las reglas recientemente.
                    results[i] = self.glossary.apply_post_correction(cached)
                    continue
            
            indices_to_translate.append(i)
            texts_to_translate.append(clean_text)

        # B. Traducir con IA lo que falta
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

                for idx_list, translation in enumerate(translated_texts):
                    original_index = indices_to_translate[idx_list]
                    original_text = texts_to_translate[idx_list]
                    
                    # 1. Guardar la traducción cruda en la DB
                    if self.tm:
                        self.tm.save(original_text, translation)
                    
                    # 2. Aplicar correcciones del Glosario antes de mostrar
                    final_text = self.glossary.apply_post_correction(translation)
                    results[original_index] = final_text

            except Exception as e:
                print(f"Error en batch: {e}")
                for idx in indices_to_translate:
                    results[idx] = texts[idx]

        return results