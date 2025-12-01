import logging

class GUILoggerHandler(logging.Handler):
    """
    Este handler intercepta los logs y los envía a la ventana de Flet
    en lugar de a la consola negra.
    """
    def __init__(self, log_widget, page):
        super().__init__()
        self.log_widget = log_widget
        self.page = page

    def emit(self, record):
        msg = self.format(record)
        # Agregamos el texto al widget de la interfaz
        self.log_widget.controls.append(logging.Text(msg, size=12, font_family="Consolas"))
        # Auto-scroll hacia abajo
        self.log_widget.scroll_to(offset=-1, duration=100)
        self.page.update()