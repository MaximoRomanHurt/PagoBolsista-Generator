"""
bolsista_controller.py
Controlador unificado para los 3 documentos de Bolsistas UNMSM con autollenado.
"""

import os
from pdf_generator import generar_declaracion_jurada, generar_informe_actividades
from docx_handler import DocumentSigner
from user_profile import UserProfile
from ui.config import OUTPUT_DIR, LOGO_PATH


class BolsistaController:
    """Gestiona la lógica de negocio, autollenado y llamado a los generadores."""

    @staticmethod
    def generar_declaracion(datos: dict) -> tuple[bool, str]:
        """Validación y generación de la Declaración Jurada."""
        nombres = datos.get("nombres", "").strip()
        ap_paterno = datos.get("ap_paterno", "").strip()
        dni = datos.get("dni", "").strip()

        if not (nombres and ap_paterno and dni):
            return False, "Los campos Nombres, Apellido Paterno y DNI son obligatorios."

        # Guardar en el perfil de autollenado
        UserProfile.guardar(datos)

        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            nom_clean = f"{ap_paterno}_{datos.get('ap_materno', '')}_{nombres}".replace(" ", "_")
            nombre_archivo = f"Declaracion_Jurada_{nom_clean}.pdf"
            ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)
            
            generar_declaracion_jurada(datos, ruta_salida, logo_path=LOGO_PATH)
            return True, ruta_salida
        except Exception as e:
            return False, f"Error al generar Declaración Jurada: {str(e)}"

    @staticmethod
    def firmar_asistencia(ruta_doc: str, ruta_firma: str) -> tuple[bool, str]:
        """Estampado de firma sobre la asistencia (salida SIEMPRE en PDF)."""
        if not ruta_doc or not os.path.exists(ruta_doc):
            return False, "Debe seleccionar un archivo de asistencia (.docx o .pdf) válido."
        if not ruta_firma or not os.path.exists(ruta_firma):
            return False, "Debe seleccionar la imagen de su firma."

        # Guardar la ruta de la firma en el perfil
        UserProfile.guardar({"firma_path": ruta_firma})

        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(ruta_doc))[0]
            nombre_salida = f"{base_name}_FIRMADO.pdf"
            ruta_salida = os.path.join(OUTPUT_DIR, nombre_salida)

            DocumentSigner.firmar_asistencia(ruta_doc, ruta_firma, ruta_salida)
            return True, ruta_salida
        except Exception as e:
            return False, f"Error al estampar firma en asistencia: {str(e)}"

    @staticmethod
    def generar_informe(datos: dict) -> tuple[bool, str]:
        """Validación y generación del Informe de Actividades."""
        de_nombre = datos.get("de_nombre", "").strip()
        para_nombre = datos.get("para_nombre", "").strip()

        if not (de_nombre and para_nombre):
            return False, "Debe completar al menos los campos 'Remitente (De:)' y 'Destinatario (A:)'."

        # Guardar en el perfil de autollenado
        UserProfile.guardar({
            "de_nombre": de_nombre,
            "para_nombre": para_nombre,
            "para_cargo": datos.get("para_cargo", ""),
            "dni": datos.get("dni", ""),
            "firma_path": datos.get("firma_path", "")
        })

        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            nom_clean = de_nombre.replace(" ", "_")
            nombre_archivo = f"Informe_Actividades_{nom_clean}.pdf"
            ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)

            generar_informe_actividades(datos, ruta_salida)
            return True, ruta_salida
        except Exception as e:
            return False, f"Error al generar Informe de Actividades: {str(e)}"
