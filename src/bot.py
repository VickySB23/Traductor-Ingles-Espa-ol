import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
from .engine import AI_Engine
from .epub_manager import EpubManager

# --- TU TOKEN PRIVADO ---
TELEGRAM_TOKEN = "8583023049:AAEdDI2knlnBQ-byTkbB_pvEs_kVh7tdV0s"

print("🤖 Iniciando cerebro del Bot...")
# Inicializamos el motor una sola vez
engine = AI_Engine(use_gpu=True) 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await update.message.reply_text(f"👋 ¡Hola {user}! Soy TranslatorLulass.\n\nEnvíame un archivo .EPUB y te lo devolveré traducido al español manteniendo el formato.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_name = doc.file_name

    # 1. Validar que sea un libro
    if not file_name.lower().endswith('.epub'):
        await update.message.reply_text("❌ Solo acepto libros en formato .EPUB")
        return

    await update.message.reply_text(f"📥 Libro recibido: {file_name}.\nProcesando... (Esto puede tardar unos minutos, paciencia 😺)")

    # 2. Preparar rutas
    os.makedirs("data/input", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    
    input_path = os.path.join("data", "input", file_name)
    output_path = os.path.join("data", "output", f"ES_{file_name}")
    
    # 3. Descargar el archivo de Telegram a tu PC
    new_file = await doc.get_file()
    await new_file.download_to_drive(input_path)

    # 4. Traducir usando tu motor local
    try:
        manager = EpubManager(input_path)
        # Usamos el motor que ya está cargado en memoria RAM
        manager.process_text(engine.translate_batch)
        manager.save(output_path)
        
        # 5. Enviar de vuelta el libro traducido
        await update.message.reply_text("✅ ¡Traducción terminada! Aquí tienes tu libro:")
        await update.message.reply_document(document=output_path)
        
    except Exception as e:
        await update.message.reply_text(f"🔥 Ocurrió un error interno: {str(e)}")
        print(f"Error bot: {e}")

def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    # Escuchar solo documentos
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print(f"🚀 TranslatorLulass_bot está escuchando... (Presiona Ctrl+C para detener)")
    app.run_polling()

if __name__ == "__main__":
    run_bot()