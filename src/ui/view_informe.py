"""
ui/view_informe.py
Vista de formulario para el Informe de Actividades con evidencias fotográficas y autollenado.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from ui.config import (
    COLOR_PRIMARIO, COLOR_HOVER, COLOR_FONDO, IMAGE_FILETYPES
)
from controllers.bolsista_controller import BolsistaController
from user_profile import UserProfile


class ViewInforme(ctk.CTkFrame):
    """Vista de formulario para redacción e inclusión de fotos en el Informe de Actividades."""

    def __init__(self, master, on_back_callback):
        super().__init__(master, fg_color=COLOR_FONDO)
        self.on_back_callback = on_back_callback
        
        self._entries = {}
        self._evidencias_paths = []
        self._var_firma = tk.StringVar(value="")
        
        self._build_ui()
        self._cargar_autollenado()

    def _build_ui(self):
        """Construye la UI del formulario de informe."""
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
            text="📊 Informe de Actividades con Evidencias Fotográficas",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_PRIMARIO
        ).pack(side="left", padx=15)

        # Botón Guardar Perfil
        ctk.CTkButton(
            top_bar,
            text="💾 Guardar Datos",
            width=110,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self._guardar_perfil_manual
        ).pack(side="right")

        # Scrollable Form Body
        form_frame = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=10)
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        form_frame.columnconfigure(1, weight=1)

        campos = [
            ("anio",        "Año", "2026"),
            ("para_nombre", "Destinatario (A:) Nombre *", "LEONEL FERNÁNDEZ ROMERO"),
            ("para_cargo",  "Destinatario Cargo / Unidad", "Jefe de la Unidad de informática de la facultad de Derecho y Ciencia Política"),
            ("de_nombre",   "Remitente (De:) Nombre *", "ROMAN HURTADO MAXIMO LENNY"),
            ("dni",         "DNI del Bolsista", "72626630"),
            ("asunto",      "Asunto", "Informe de actividades"),
            ("fecha",       "Fecha del informe", "Lima, 30 de Abril de 2026"),
            ("fecha_inicio","Inicio de servicio", "01 de Abril"),
        ]

        for idx, (key, label, placeholder) in enumerate(campos):
            ctk.CTkLabel(
                form_frame, text=label,
                font=ctk.CTkFont(weight="bold", size=12)
            ).grid(row=idx, column=0, sticky="w", padx=15, pady=(8, 2))

            entry = ctk.CTkEntry(form_frame, placeholder_text=placeholder)
            entry.grid(row=idx, column=1, sticky="ew", padx=15, pady=(8, 2))
            self._entries[key] = entry

        # Textbox de Actividades (una por línea)
        row_act = len(campos)
        ctk.CTkLabel(
            form_frame, text="Actividades Realizadas\n(Una por línea) *",
            font=ctk.CTkFont(weight="bold", size=12)
        ).grid(row=row_act, column=0, sticky="nw", padx=15, pady=(8, 2))

        self.tb_actividades = ctk.CTkTextbox(form_frame, height=90)
        self.tb_actividades.grid(row=row_act, column=1, sticky="ew", padx=15, pady=(8, 2))
        self.tb_actividades.insert("1.0", "Atención técnica de soporte a los profesores y administrativos.\nMantenimiento e Instalación de equipo de laboratorio.")

        # Sección de Fotos / Evidencias
        row_fotos = row_act + 1
        ctk.CTkLabel(
            form_frame, text="Evidencias Fotográficas",
            font=ctk.CTkFont(weight="bold", size=12)
        ).grid(row=row_fotos, column=0, sticky="w", padx=15, pady=(12, 2))

        box_fotos = ctk.CTkFrame(form_frame, fg_color="transparent")
        box_fotos.grid(row=row_fotos, column=1, sticky="ew", padx=15, pady=(12, 2))
        
        self.lbl_fotos = ctk.CTkLabel(box_fotos, text="No se han añadido fotos.", font=ctk.CTkFont(size=11), text_color="#555555")
        self.lbl_fotos.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            box_fotos, text="➕ Añadir Fotos", width=110,
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
            command=self._aniadir_fotos
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            box_fotos, text="🗑️ Limpiar", width=80,
            fg_color="#B22222", hover_color="#8B0000",
            command=self._limpiar_fotos
        ).pack(side="left", padx=5)

        # Campo de Firma
        row_firma = row_fotos + 1
        ctk.CTkLabel(
            form_frame, text="Imagen de Firma",
            font=ctk.CTkFont(weight="bold", size=12)
        ).grid(row=row_firma, column=0, sticky="w", padx=15, pady=(12, 2))

        box_firma = ctk.CTkFrame(form_frame, fg_color="transparent")
        box_firma.grid(row=row_firma, column=1, sticky="ew", padx=15, pady=(12, 2))
        box_firma.columnconfigure(0, weight=1)

        ctk.CTkEntry(box_firma, textvariable=self._var_firma, state="readonly").grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(
            box_firma, text="📂 Buscar Firma", width=110,
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
            command=self._buscar_firma
        ).grid(row=0, column=1)

        # Botón Generar PDF
        ctk.CTkButton(
            form_frame,
            text="⚡ Generar Informe de Actividades (PDF)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLOR_PRIMARIO,
            hover_color=COLOR_HOVER,
            height=40,
            command=self._generar
        ).grid(row=row_firma + 1, column=0, columnspan=2, padx=15, pady=25, sticky="ew")

    def _cargar_autollenado(self):
        """Carga datos guardados en el perfil de usuario."""
        profile = UserProfile.cargar()

        # Mapear datos guardados
        if profile.get("de_nombre") and not self._entries["de_nombre"].get():
            self._entries["de_nombre"].insert(0, profile["de_nombre"])
        elif profile.get("nombres") and profile.get("ap_paterno"):
            full_nom = f"{profile.get('ap_paterno', '')} {profile.get('ap_materno', '')} {profile.get('nombres', '')}".strip()
            self._entries["de_nombre"].insert(0, full_nom)

        if profile.get("para_nombre"):
            self._entries["para_nombre"].insert(0, profile["para_nombre"])
        if profile.get("para_cargo"):
            self._entries["para_cargo"].insert(0, profile["para_cargo"])
        if profile.get("dni"):
            self._entries["dni"].insert(0, profile["dni"])
        if profile.get("firma_path"):
            self._var_firma.set(profile["firma_path"])

    def _guardar_perfil_manual(self):
        """Guarda manualmente los datos ingresados."""
        UserProfile.guardar({
            "de_nombre": self._entries["de_nombre"].get().strip(),
            "para_nombre": self._entries["para_nombre"].get().strip(),
            "para_cargo": self._entries["para_cargo"].get().strip(),
            "dni": self._entries["dni"].get().strip(),
            "firma_path": self._var_firma.get() or None
        })
        messagebox.showinfo("💾 Autollenado Guardado", "Tus datos se han guardado exitosamente para futuros informes.")

    def _aniadir_fotos(self):
        """Diálogo para seleccionar varias imágenes."""
        rutas = filedialog.askopenfilenames(
            title="Seleccionar imágenes de evidencia",
            filetypes=IMAGE_FILETYPES
        )
        if rutas:
            self._evidencias_paths.extend(rutas)
            cant = len(self._evidencias_paths)
            self.lbl_fotos.configure(text=f"📷 {cant} foto(s) seleccionada(s).")

    def _limpiar_fotos(self):
        """Limpia la lista de imágenes seleccionadas."""
        self._evidencias_paths.clear()
        self.lbl_fotos.configure(text="No se han añadido fotos.")

    def _buscar_firma(self):
        """Diálogo para seleccionar la firma."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen de la firma",
            filetypes=IMAGE_FILETYPES
        )
        if ruta:
            self._var_firma.set(ruta)

    def _generar(self):
        """Envía los datos al controlador para crear el PDF."""
        datos = {key: entry.get().strip() for key, entry in self._entries.items()}
        datos["actividades"] = self.tb_actividades.get("1.0", "end").strip()
        datos["evidencias"] = self._evidencias_paths
        datos["firma_path"] = self._var_firma.get() or None

        exito, resultado = BolsistaController.generar_informe(datos)
        if exito:
            messagebox.showinfo("✅ Éxito", f"Informe de Actividades generado exitosamente:\n\n{resultado}")
        else:
            messagebox.showerror("Error", resultado)
