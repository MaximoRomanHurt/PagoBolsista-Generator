"""
main.py
Punto de entrada principal: Sistema de Documentos de Pago para Bolsistas UNMSM.
"""

import os
import sys
import customtkinter as ctk

# Agregar src/ al path para importaciones relativas
sys.path.insert(0, os.path.dirname(__file__))

from ui.config import (
    COLOR_PRIMARIO, COLOR_FONDO, WINDOW_WIDTH, WINDOW_HEIGHT, OUTPUT_DIR
)
from ui.utils import obtener_posicion_ventana_centrada
from ui.view_seleccion import ViewSeleccion
from ui.view_declaracion import ViewDeclaracion
from ui.view_asistencia import ViewAsistencia
from ui.view_informe import ViewInforme

# ── Configuración de Tema CustomTkinter ──────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """Aplicación principal con navegador de pantallas."""

    def __init__(self):
        super().__init__()
        self.title("Generador de Documentos de Pago para Bolsistas — UNMSM")

        # Centrado de ventana en pantalla
        x, y, _, _ = obtener_posicion_ventana_centrada()
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.resizable(True, True)
        self.configure(fg_color=COLOR_FONDO)

        self._active_view = None
        self._build_ui()
        self.mostrar_seleccion()

    def _build_ui(self):
        """Header principal y contenedor de vistas."""
        # Header Superior
        header = ctk.CTkFrame(self, fg_color=COLOR_PRIMARIO, corner_radius=0, height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="  🏛️ UNMSM — Documentos de Pago para Bolsistas",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=18)

        # Contenedor dinámico principal
        self.container = ctk.CTkFrame(self, fg_color=COLOR_FONDO)
        self.container.pack(fill="both", expand=True)

    def _cambiar_vista(self, nueva_vista_class, *args):
        """Reemplaza la vista activa por una nueva."""
        if self._active_view is not None:
            self._active_view.destroy()
        self._active_view = nueva_vista_class(self.container, *args)
        self._active_view.pack(fill="both", expand=True)

    def mostrar_seleccion(self):
        """Muestra la pantalla inicial de los 3 documentos."""
        self._cambiar_vista(ViewSeleccion, self.on_documento_seleccionado)

    def on_documento_seleccionado(self, doc_id: str):
        """Maneja la transición al formulario del documento elegido."""
        if doc_id == "declaracion":
            self._cambiar_vista(ViewDeclaracion, self.mostrar_seleccion)
        elif doc_id == "asistencia":
            self._cambiar_vista(ViewAsistencia, self.mostrar_seleccion)
        elif doc_id == "informe":
            self._cambiar_vista(ViewInforme, self.mostrar_seleccion)


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app = App()
    app.mainloop()