"""
bolsista_controller.py
Controlador unificado para los 3 documentos de Bolsistas UNMSM con autollenado.
"""

import os
import re
import unicodedata
from pdf_generator import generar_declaracion_jurada, generar_informe_actividades
from docx_handler import DocumentSigner
from user_profile import UserProfile
from ui.config import OUTPUT_DIR, LOGO_PATH


class BolsistaController:
    """Gestiona la lógica de negocio, autollenado y llamado a los generadores."""

    @staticmethod
    def _normalizar_fragmento_nombre(valor: str) -> str:
        texto = unicodedata.normalize("NFKD", str(valor or ""))
        texto = texto.encode("ascii", "ignore").decode("ascii")
        texto = re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_").lower()
        return texto or "usuario"

    @staticmethod
    def build_output_name(document_type: str, datos: dict) -> str:
        tipo = (document_type or "documento").strip().lower()
        if datos.get("de_nombre", "").strip():
            nombre_usuario = datos["de_nombre"].strip()
        else:
            nombre_usuario = " ".join(
                str(datos.get(campo, "")).strip()
                for campo in ("ap_paterno", "ap_materno", "nombres")
                if str(datos.get(campo, "")).strip()
            )
        nombre_seguro = BolsistaController._normalizar_fragmento_nombre(nombre_usuario)
        prefijos = {
            "declaracion": "declaracion_jurada",
            "asistencia": "reporte_asistencia",
            "informe": "informe_actividades",
        }
        return f"{prefijos.get(tipo, tipo)}_{nombre_seguro}.pdf"

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
            nombre_archivo = BolsistaController.build_output_name("declaracion", datos)
            ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)
            
            generar_declaracion_jurada(datos, ruta_salida, logo_path=LOGO_PATH)
            return True, ruta_salida
        except Exception as e:
            return False, f"Error al generar Declaración Jurada: {str(e)}"

    @staticmethod
    def firmar_asistencia(ruta_doc: str, ruta_firma: str, datos: dict | None = None) -> tuple[bool, str]:
        """Estampado de firma sobre la asistencia (salida SIEMPRE en PDF)."""
        datos = datos or {}
        if not ruta_doc or not os.path.exists(ruta_doc):
            return False, "Debe seleccionar un archivo de asistencia (.docx o .pdf) válido."
        if not ruta_firma or not os.path.exists(ruta_firma):
            return False, "Debe seleccionar la imagen de su firma."
        if not all(str(datos.get(campo, "")).strip() for campo in ("ap_paterno", "ap_materno", "nombres")):
            return False, "Los campos Nombres, Apellido Paterno y Apellido Materno son obligatorios."

        # Guardar la ruta de la firma en el perfil
        UserProfile.guardar({"firma_path": ruta_firma})

        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            perfil = UserProfile.cargar()
            nombre_salida = BolsistaController.build_output_name("asistencia", {**perfil, **datos})
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
            nombre_archivo = BolsistaController.build_output_name("informe", datos)
            ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)

            generar_informe_actividades(datos, ruta_salida)
            return True, ruta_salida
        except Exception as e:
            return False, f"Error al generar Informe de Actividades: {str(e)}"
