import flet as ft
import threading
import time
import os
from .engine import AI_Engine
from .epub_manager import EpubManager
from .tm_manager import TranslationMemory
from .config import DEFAULT_MODEL

# Variables globales para el estado
current_file_path = None

def main(page: ft.Page):
    # --- Configuración de la Ventana ---
    page.title = "Traductor de Libros Pro AI"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_height = 700
    page.window_resizable = False
    page.padding = 20

    # --- Elementos de la UI ---
    
    # 1. Título y Header
    # Usamos strings ("blue200") para compatibilidad universal
    header = ft.Text("Traductor AI Local", size=30, weight=ft.FontWeight.BOLD, color="blue200")
    sub_header = ft.Text("Inglés -> Español | Preservando formato", size=14, color="grey400")

    # 2. Selector de Archivos
    lbl_selected_file = ft.Text("Ningún archivo seleccionado", italic=True, color="grey500")
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        global current_file_path
        if e.files:
            file = e.files[0]
            current_file_path = file.path
            lbl_selected_file.value = f"📁 {file.name}"
            lbl_selected_file.color = "white"
            btn_start.disabled = False 
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    
    btn_select = ft.ElevatedButton(
        "Seleccionar EPUB",
        icon="upload_file",  # <--- CAMBIO AQUÍ (Texto en lugar de objeto)
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["epub"]),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    # 3. Opciones (Switches)
    sw_gpu = ft.Switch(label="Usar GPU (Aceleración)", value=True)
    sw_tm = ft.Switch(label="Memoria de Traducción (Cache)", value=True)
    
    # 4. Barra de Progreso
    progress_bar = ft.ProgressBar(width=560, value=0, visible=False)
    lbl_status = ft.Text("", size=12)

    # 5. Consola Visual (Logs)
    log_column = ft.Column(scroll=ft.ScrollMode.ALWAYS, auto_scroll=True)
    log_container = ft.Container(
        content=log_column,
        height=200,
        bgcolor="black38",
        border_radius=10,
        padding=10,
        border=ft.border.all(1, "grey800")
    )

    # --- Lógica de Traducción en Segundo Plano ---
    def run_translation_thread():
        # Desactivar controles
        btn_start.disabled = True
        btn_select.disabled = True
        progress_bar.visible = True
        # Usamos try-except por si la versión de Flet es muy antigua para ProgressBarOperation
        try:
            progress_bar.type = ft.ProgressBarOperation.INDETERMINATE 
        except:
            pass # Si falla, simplemente se queda como barra normal
        page.update()

        try:
            log_msg("🚀 Iniciando motor de IA...", "cyan")
            
            # Inicializar componentes
            tm = TranslationMemory() if sw_tm.value else None
            engine = AI_Engine(use_gpu=sw_gpu.value, tm=tm)
            
            # Definir salida
            base, ext = os.path.splitext(current_file_path)
            output_file = f"{base}_ES{ext}"

            log_msg(f"📖 Leyendo libro: {os.path.basename(current_file_path)}")
            epub_mgr = EpubManager(current_file_path)

            try:
                progress_bar.type = ft.ProgressBarOperation.DETERMINATE 
            except:
                pass

            log_msg("⚡ Traduciendo capítulos... (Esto puede tardar)", "yellow")
            
            epub_mgr.process_text(engine.translate_batch, logger=None) 
            
            log_msg("💾 Guardando archivo final...")
            epub_mgr.save(output_file)

            if tm: tm.close()

            log_msg(f"✅ ¡COMPLETADO! Guardado en: {os.path.basename(output_file)}", "green")
            progress_bar.value = 1
            
        except Exception as e:
            log_msg(f"❌ Error: {str(e)}", "red")
        
        finally:
            btn_start.disabled = False
            btn_select.disabled = False
            page.update()

    def on_start_click(e):
        if not current_file_path:
            return
        threading.Thread(target=run_translation_thread, daemon=True).start()

    def log_msg(text, color="white"):
        log_column.controls.append(ft.Text(f"> {text}", color=color, font_family="Consolas", size=12))
        page.update()

    btn_start = ft.ElevatedButton(
        "COMENZAR TRADUCCIÓN",
        icon="play_arrow",  # <--- CAMBIO AQUÍ (Texto en lugar de objeto)
        style=ft.ButtonStyle(
            color="white",
            bgcolor="blue700",
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=20,
        ),
        width=560,
        disabled=True,
        on_click=on_start_click
    )

    # --- Armado de la Pantalla ---
    page.add(
        header,
        sub_header,
        ft.Divider(height=20, color="transparent"),
        ft.Row([btn_select, lbl_selected_file], alignment=ft.MainAxisAlignment.START),
        ft.Divider(height=10, color="transparent"),
        ft.Container(
            content=ft.Column([sw_gpu, sw_tm]),
            bgcolor="grey900",
            padding=10,
            border_radius=10
        ),
        ft.Divider(height=20, color="transparent"),
        btn_start,
        ft.Divider(height=10, color="transparent"),
        lbl_status,
        progress_bar,
        ft.Text("Registro de actividad:", size=12, color="grey500"),
        log_container
    )

if __name__ == "__main__":
    ft.app(target=main)