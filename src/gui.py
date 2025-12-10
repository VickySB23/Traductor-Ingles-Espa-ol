import flet as ft
import threading
import os
from .engine import AI_Engine
from .epub_manager import EpubManager
from .tm_manager import TranslationMemory

# --- ESTADO GLOBAL ---
engine = None
tm = None

def main(page: ft.Page):
    page.title = "Translator Dashboard"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_min_width = 800
    page.window_min_height = 600

    # --- Estilos y Componentes ---
    def create_card(content_control):
        return ft.Container(
            content=content_control,
            padding=20,
            bgcolor="grey900", 
            border_radius=15,
            expand=True,
        )

    # ==========================
    # VISTA 1: TRADUCTOR RÁPIDO
    # ==========================
    txt_input = ft.TextField(
        label="Inglés (Original)", multiline=True, min_lines=10, max_lines=10, 
        expand=True, border_color="transparent", bgcolor="black26"
    )
    txt_output = ft.TextField(
        label="Español (Traducción)", multiline=True, min_lines=10, max_lines=10, 
        expand=True, read_only=True, border_color="transparent", bgcolor="black26"
    )

    def traducir_texto_click(e):
        if not engine:
            snack("⚠️ Primero carga el motor en Ajustes", "red")
            return
        if not txt_input.value: return
        
        btn_traducir_txt.disabled = True
        btn_traducir_txt.text = "Procesando..."
        page.update()

        def _task():
            try:
                # Enviamos lista de 1 elemento
                res = engine.translate_batch([txt_input.value])
                txt_output.value = res[0]
            except Exception as ex:
                txt_output.value = f"Error: {ex}"
            
            btn_traducir_txt.disabled = False
            btn_traducir_txt.text = "Traducir Texto"
            page.update()

        threading.Thread(target=_task, daemon=True).start()

    btn_traducir_txt = ft.ElevatedButton("Traducir Texto", icon="translate", on_click=traducir_texto_click, bgcolor="blue700", color="white", height=50)

    # FIX: Usamos Container para el padding
    view_text = ft.Container(
        content=ft.Column([
            ft.Text("Traductor Rápido", size=25, weight="bold"),
            ft.Row([create_card(txt_input), ft.Icon("arrow_forward", color="grey500"), create_card(txt_output)], expand=True),
            ft.Container(btn_traducir_txt, alignment=ft.alignment.center_right)
        ], expand=True),
        padding=20,
        expand=True
    )

    # ==========================
    # VISTA 2: LIBROS (EPUB)
    # ==========================
    lbl_file = ft.Text("Ningún archivo seleccionado", italic=True)
    pb_file = ft.ProgressBar(width=400, visible=False)
    log_view = ft.Column(scroll="always", auto_scroll=True)
    current_file = {"path": None} 

    def pick_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            current_file["path"] = e.files[0].path
            lbl_file.value = e.files[0].name
            lbl_file.color = "white"
            btn_file_start.disabled = False
            page.update()

    file_picker = ft.FilePicker(on_result=pick_file_result)
    page.overlay.append(file_picker)

    def log_gui(msg, color="white"):
        # Esta función maneja correctamente el mensaje Y el color (opcional)
        # Si llega un segundo argumento color, lo usa. Si no, usa white.
        log_view.controls.append(ft.Text(f"> {msg}", color=color, font_family="Consolas"))
        page.update()

    def procesar_libro_click(e):
        if not engine:
            snack("⚠️ Motor apagado. Ve a Ajustes.", "red")
            return
        
        btn_file_start.disabled = True
        pb_file.visible = True
        page.update()

        def _task_epub():
            try:
                input_path = current_file["path"]
                base, ext = os.path.splitext(input_path)
                output_path = f"{base}_ES{ext}"
                
                log_gui(f"📖 Leyendo: {os.path.basename(input_path)}", "cyan")
                manager = EpubManager(input_path)
                
                log_gui("⚡ Traduciendo... (Mira la terminal para detalle)", "yellow")
                
                # FIX: Pasamos log_gui directamente. 
                # Ahora acepta los argumentos (msg, color) que envía el EpubManager
                manager.process_text(engine.translate_batch, logger=log_gui) 
                
                log_gui("💾 Guardando...", "cyan")
                manager.save(output_path)
                log_gui(f"✅ ¡LISTO! {os.path.basename(output_path)}", "green")
                snack("Libro traducido con éxito", "green")

            except Exception as ex:
                log_gui(f"❌ Error: {ex}", "red")
            
            btn_file_start.disabled = False
            pb_file.visible = False
            page.update()

        threading.Thread(target=_task_epub, daemon=True).start()

    btn_file_start = ft.ElevatedButton("Comenzar Traducción", icon="play_arrow", disabled=True, on_click=procesar_libro_click, bgcolor="blue700", color="white")

    view_books = ft.Container(
        content=ft.Column([
            ft.Text("Traductor de Libros", size=25, weight="bold"),
            create_card(ft.Column([
                ft.Text("Sube tu archivo .EPUB", color="grey400"),
                ft.Row([ft.ElevatedButton("Seleccionar", icon="upload_file", on_click=lambda _: file_picker.pick_files(allowed_extensions=["epub"])), lbl_file]),
                ft.Divider(),
                btn_file_start,
                pb_file,
                ft.Container(height=200, content=log_view, bgcolor="black", border_radius=10, padding=10, margin=ft.margin.only(top=10))
            ]))
        ], expand=True),
        padding=20,
        expand=True
    )

    # ==========================
    # VISTA 3: AJUSTES (MOTOR)
    # ==========================
    sw_gpu = ft.Switch(label="Usar GPU (NVIDIA)", value=True)
    sw_tm = ft.Switch(label="Usar Memoria de Traducción (Cache)", value=True)
    lbl_status = ft.Text("Estado: MOTOR APAGADO", color="red", weight="bold", size=20)

    def init_engine(e):
        global engine, tm
        lbl_status.value = "Cargando modelo... (Espera)"
        lbl_status.color = "yellow"
        btn_init.disabled = True
        page.update()

        def _load():
            global engine, tm
            try:
                tm = TranslationMemory() if sw_tm.value else None
                engine = AI_Engine(use_gpu=sw_gpu.value, tm=tm)
                lbl_status.value = f"Estado: LISTO ({engine.device.upper()})"
                lbl_status.color = "green"
                snack("Motor cargado correctamente", "green")
            except Exception as ex:
                lbl_status.value = f"Error: {ex}"
                lbl_status.color = "red"
                btn_init.disabled = False
            page.update()
        
        threading.Thread(target=_load, daemon=True).start()

    btn_init = ft.ElevatedButton("ENCENDER MOTOR", icon="power_settings_new", on_click=init_engine, bgcolor="green700", color="white", height=60)

    view_config = ft.Container(
        content=ft.Column([
            ft.Text("Configuración", size=25, weight="bold"),
            create_card(ft.Column([
                ft.Text("Control del Motor AI", size=18, weight="bold"),
                sw_gpu, sw_tm,
                ft.Divider(height=20),
                btn_init,
                ft.Divider(height=20),
                lbl_status
            ]))
        ], expand=True),
        padding=20,
        expand=True
    )

    # --- NAVEGACIÓN ---
    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0: content_area.content = view_text
        elif idx == 1: content_area.content = view_books
        elif idx == 2: content_area.content = view_config
        page.update()

    rail = ft.NavigationRail(
        selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=100,
        destinations=[
            ft.NavigationRailDestination(icon="translate", label="Texto"),
            ft.NavigationRailDestination(icon="book", label="Libros"),
            ft.NavigationRailDestination(icon="settings", label="Ajustes"),
        ], on_change=nav_change
    )

    content_area = ft.Container(content=view_text, expand=True)
    page.add(ft.Row([rail, ft.VerticalDivider(width=1), content_area], expand=True))

    def snack(text, color):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

if __name__ == "__main__":
    ft.app(target=main)