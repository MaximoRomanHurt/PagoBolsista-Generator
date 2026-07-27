"""
ui/view_seleccion.py
Pantalla de inicio: Selección entre los 3 documentos para Bolsistas UNMSM.
"""

import customtkinter as ctk
from ui.config import (
    COLOR_PRIMARIO, COLOR_HOVER, COLOR_SEGUNDARIO, COLOR_FONDO,
    COLOR_TARJETA, COLOR_TEXTO
)


class ViewSeleccion(ctk.CTkFrame):
    """Pantalla inicial de selección de documentos."""

    def __init__(self, master, on_select_callback):
        super().__init__(master, fg_color=COLOR_FONDO)
        self.on_select_callback = on_select_callback
        self._build_ui()

    def _build_ui(self):
        """Construye las tarjetas de selección."""
        # Título principal
        ctk.CTkLabel(
            self,
            text="🎓 Generador de Documentos para Bolsistas UNMSM",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLOR_PRIMARIO
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self,
            text="Seleccione el documento de pago que desea generar o firmar:",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_TEXTO
        ).pack(pady=(0, 25))

        # Contenedor de las 3 Tarjetas
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=25, pady=10)
        cards_frame.columnconfigure((0, 1, 2), weight=1, uniform="card")
        cards_frame.rowconfigure(0, weight=1)

        # Configuración de los 3 documentos
        documentos = [
            {
                "id": "declaracion",
                "icono": "📜",
                "titulo": "Declaración Jurada",
                "subtitulo": "Ley N° 30220",
                "desc": "Declaración de no pertenecer a órganos de gobierno de la UNMSM.\n\nFormulario con datos personales, fecha y firma.",
                "boton": "Llenar Declaración"
            },
            {
                "id": "asistencia",
                "icono": "📅",
                "titulo": "Reporte de Asistencias",
                "subtitulo": "Firma en DOCX / PDF",
                "desc": "Selecciona el documento de asistencia enviado por tu facultad y estampa tu firma automáticamente.",
                "boton": "Firmar Asistencia"
            },
            {
                "id": "informe",
                "icono": "📊",
                "titulo": "Informe de Actividades",
                "subtitulo": "Con Evidencias Fotográficas",
                "desc": "Informe formal con lista de actividades realizadas y grilla de fotos/evidencias adjuntas.",
                "boton": "Redactar Informe"
            }
        ]

        for idx, doc in enumerate(documentos):
            card = ctk.CTkFrame(
                cards_frame,
                fg_color=COLOR_TARJETA,
                corner_radius=12,
                border_width=2,
                border_color="#E0E0E0"
            )
            card.grid(row=0, column=idx, padx=10, pady=10, sticky="nsew")

            # Icono
            ctk.CTkLabel(
                card,
                text=doc["icono"],
                font=ctk.CTkFont(size=40)
            ).pack(pady=(20, 5))

            # Título y Subtítulo
            ctk.CTkLabel(
                card,
                text=doc["titulo"],
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=COLOR_PRIMARIO
            ).pack(pady=(0, 2))

            ctk.CTkLabel(
                card,
                text=doc["subtitulo"],
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#666666"
            ).pack(pady=(0, 10))

            # Descripción
            ctk.CTkLabel(
                card,
                text=doc["desc"],
                font=ctk.CTkFont(size=11),
                text_color="#444444",
                wraplength=200,
                justify="center"
            ).pack(pady=(0, 20), padx=10, expand=True)

            # Botón de Acción
            doc_id = doc["id"]
            btn = ctk.CTkButton(
                card,
                text=doc["boton"],
                fg_color=COLOR_PRIMARIO,
                hover_color=COLOR_HOVER,
                font=ctk.CTkFont(size=12, weight="bold"),
                corner_radius=8,
                height=36,
                command=lambda d=doc_id: self.on_select_callback(d)
            )
            btn.pack(pady=(0, 20), padx=15, fill="x")
