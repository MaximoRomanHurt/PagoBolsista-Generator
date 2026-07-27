"""
ui/view_asistencia.py
Vista para estampar la firma en el Reporte de Asistencia (Salida obligatoria en PDF).
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from ui.config import (
    COLOR_PRIMARIO, COLOR_HOVER, COLOR_FONDO, IMAGE_FILETYPES, DOCX_PDF_FILETYPES
)
from controllers.bolsista_controller import BolsistaController
from user_profile import UserProfile


class ViewAsistencia(ctk.CTkFrame):
    """Vista para cargar el reporte de asistencia y colocar la firma."""

    def __init__(self, master, on_back_callback):
        super().__init__(master, fg_color=COLOR_FONDO)
        self.on_back_callback = on_back_callback
        
        self._var_doc = tk.StringVar(value="")
        self._var_firma = tk.StringVar(value="")
        
        self._build_ui()
        self._cargar_autollenado()

    def _build_ui(self):
        """Construye la UI."""
        # Top Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkButton(
            top_bar,
            text="← Volver",
            width=90,
            fg_color="#555555",
            hover_color="#333333",
            command=self.on_back_callback
        ).pack(side="left")

        ctk.CTkLabel(
            top_bar,
            text="📅 Reporte de Asistencias — Estampado de Firma",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_PRIMARIO
        ).pack(side="left", padx=15)

        # Main Body Frame
        body_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=10)
        body_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        body_frame.columnconfigure(1, weight=1)

        # Nota informativa
        info_box = ctk.CTkFrame(body_frame, fg_color="#F0F4F8", corner_radius=8)
        info_box.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        ctk.CTkLabel(
            info_box,
            text="ℹ️ El documento de asistencia no sufrirá alteraciones en sus datos ni en las celdas.\n"
                 "La firma se colocará exactamente dentro de las casillas y el resultado será SIEMPRE un archivo PDF.",
            font=ctk.CTkFont(size=12),
            text_color="#1F3A60",
            justify="left"
        ).pack(padx=15, pady=12)

        # 1. Seleccionar archivo DOCX / PDF
        ctk.CTkLabel(
            body_frame, text="1. Archivo de Asistencia (DOCX / PDF) *",
            font=ctk.CTkFont(weight="bold", size=12)
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(15, 5))

        box_doc = ctk.CTkFrame(body_frame, fg_color="transparent")
        box_doc.grid(row=1, column=1, sticky="ew", padx=20, pady=(15, 5))
        box_doc.columnconfigure(0, weight=1)

        ctk.CTkEntry(box_doc, textvariable=self._var_doc, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            box_doc, text="📂 Buscar DOCX/PDF", width=140,
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
            command=self._buscar_doc
        ).grid(row=0, column=1)

        # 2. Seleccionar Imagen de Firma
        ctk.CTkLabel(
            body_frame, text="2. Imagen de tu Firma *",
            font=ctk.CTkFont(weight="bold", size=12)
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(15, 5))

        box_firma = ctk.CTkFrame(body_frame, fg_color="transparent")
        box_firma.grid(row=2, column=1, sticky="ew", padx=20, pady=(15, 5))
        box_firma.columnconfigure(0, weight=1)

        ctk.CTkEntry(box_firma, textvariable=self._var_firma, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            box_firma, text="📂 Buscar Firma", width=140,
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
            command=self._buscar_firma
        ).grid(row=0, column=1)

        # Botón Acción Principal
        ctk.CTkButton(
            body_frame,
            text="✍️ Estampar Firma y Exportar a PDF",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_PRIMARIO,
            hover_color=COLOR_HOVER,
            height=44,
            command=self._firmar
        ).grid(row=3, column=0, columnspan=2, padx=20, pady=35, sticky="ew")

    def _cargar_autollenado(self):
        """Carga la firma previamente guardada."""
        profile = UserProfile.cargar()
        if profile.get("firma_path"):
            self._var_firma.set(profile["firma_path"])

    def _buscar_doc(self):
        """Diálogo para buscar el archivo de asistencia."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de asistencia",
            filetypes=DOCX_PDF_FILETYPES
        )
        if ruta:
            self._var_doc.set(ruta)

    def _buscar_firma(self):
        """Diálogo para buscar la firma."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen de la firma",
            filetypes=IMAGE_FILETYPES
        )
        if ruta:
            self._var_firma.set(ruta)

    def _firmar(self):
        """Ejecuta el estampado de firma."""
        doc = self._var_doc.get().strip()
        firma = self._var_firma.get().strip()

        exito, resultado = BolsistaController.firmar_asistencia(doc, firma)
        if exito:
            messagebox.showinfo("✅ Firma Completada", f"Documento firmado guardado en formato PDF:\n\n{resultado}")
        else:
            messagebox.showerror("Error", resultado)
