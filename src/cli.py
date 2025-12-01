import typer
import os
import time
from .engine import AI_Engine
from .epub_manager import EpubManager
from .tm_manager import TranslationMemory
from .utils import setup_logger, get_file_hash
from .config import BATCH_SIZE

app = typer.Typer()
logger = setup_logger()

@app.command()
def start(
    input_file: str = typer.Option(..., "--input", "-i", help="Ruta al archivo .epub"),
    output_file: str = typer.Option(None, "--output", "-o", help="Ruta de salida (opcional)"),
    force: bool = typer.Option(False, "--force", "-f", help="Sobrescribir archivo existente"),
    use_gpu: bool = typer.Option(True, "--gpu/--cpu", help="Usar aceleración GPU"),
    use_tm: bool = typer.Option(True, "--tm/--no-tm", help="Usar Memoria de Traducción")
):
    """
    Inicia la traducción de un EPUB manteniendo formato e imágenes.
    """
    # 1. Validaciones
    if not os.path.exists(input_file):
        typer.secho(f"❌ Error: No existe {input_file}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_ES{ext}"

    if os.path.exists(output_file) and not force:
        typer.secho(f"⚠️  El archivo {output_file} ya existe. Usa --force para sobrescribir.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

    # 2. Inicio
    logger.info(f"Iniciando tarea: {input_file}")
    typer.secho("🚀 Cargando componentes...", fg=typer.colors.CYAN)
    
    start_time = time.time()

    # 3. Componentes
    tm = TranslationMemory() if use_tm else None
    engine = AI_Engine(use_gpu=use_gpu, tm=tm)
    epub_mgr = EpubManager(input_file)

    # 4. Procesamiento
    try:
        epub_mgr.process_text(engine.translate_batch, logger)
        
        # 5. Guardado
        typer.secho("💾 Guardando archivo...", fg=typer.colors.CYAN)
        epub_mgr.save(output_file)
        
        if tm: tm.close()
        
        duration = round(time.time() - start_time, 2)
        typer.secho(f"\n✅ ¡Éxito! Guardado en: {output_file}", fg=typer.colors.GREEN, bold=True)
        typer.echo(f"⏱️  Tiempo total: {duration}s")
        
    except Exception as e:
        logger.error(f"Fallo crítico: {e}")
        typer.secho(f"\n❌ Error crítico: {e}", fg=typer.colors.RED)