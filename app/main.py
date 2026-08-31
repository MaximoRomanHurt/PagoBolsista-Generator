"""
app/main.py
Servidor FastAPI para la versión WEB del Generador de Documentos de Pago — UNMSM.
"""

import os
import re
import sys
import tempfile
import shutil
import unicodedata
from typing import List, Optional
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Asegurar que el directorio raíz y src/ estén en el path de Python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from pdf_generator import generar_declaracion_jurada, generar_informe_actividades
from docx_handler import DocumentSigner

app = FastAPI(
    title="UNMSM · Mesa de Trámites — Bolsistas",
    description="Sistema Web para generación y firmado de documentos de cobro de bolsistas UNMSM."
)

# Montar archivos estáticos (CSS / JS)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Configurar motor de plantillas Jinja2
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def _normalizar_nombre_archivo(texto: str) -> str:
    """Normaliza un nombre para el archivo: sin tildes, sin espacios raros y con guiones bajos."""
    texto = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode("ascii")
    texto = texto.strip().upper()
    texto = re.sub(r"[^A-Z0-9]+", "_", texto)
    return texto.strip("_") or "USUARIO"


def _extraer_nombre_desde_documento(doc_path: str) -> str:
    """Intenta recuperar el nombre del alumno desde el contenido del documento PDF/DOCX."""
    texto_total = ""

    try:
        import fitz
        with fitz.open(doc_path) as documento:
            for pagina in documento:
                texto_total += "\n" + (pagina.get_text("text") or "")
    except Exception:
        texto_total = ""

    if not texto_total:
        try:
            import pypdf
            reader = pypdf.PdfReader(doc_path)
            for pagina in reader.pages:
                texto_total += "\n" + (pagina.extract_text() or "")
        except Exception:
            texto_total = ""

    if not texto_total and doc_path.lower().endswith(".docx"):
        try:
            import docx
            documento = docx.Document(doc_path)
            texto_total = "\n".join(parrafo.text for parrafo in documento.paragraphs)
        except Exception:
            texto_total = ""

    if not texto_total:
        return "USUARIO"

    match = re.search(r"ALUMNO\s*[:.-]?\s*(.+)", texto_total, flags=re.IGNORECASE)
    nombre_raw = match.group(1).strip() if match else texto_total.strip()
    nombre_raw = nombre_raw.replace(",", " ")
    nombre_raw = re.sub(r"\s+", " ", nombre_raw).strip()
    nombre_raw = unicodedata.normalize("NFKD", nombre_raw).encode("ascii", "ignore").decode("ascii")
    nombre_raw = re.sub(r"[^A-Za-z0-9 ]+", " ", nombre_raw)
    nombre_limpio = "_".join(nombre_raw.upper().split())
    return nombre_limpio or "USUARIO"


def _nombre_archivo_usuario(prefijo: str, nombres: str = "", ap_paterno: str = "", ap_materno: str = "", nombre_completo: str = "") -> str:
    """Construye un nombre de descarga con el formato APELLIDOS_NOMBRES_TIPO.pdf."""
    if any((ap_paterno, ap_materno, nombres)):
        partes = [ap_paterno, ap_materno, nombres]
    else:
        partes = [nombre_completo]

    nombre_base = " ".join(str(parte).strip() for parte in partes if str(parte).strip())
    nombre_normalizado = _normalizar_nombre_archivo(nombre_base)
    prefijo_normalizado = _normalizar_nombre_archivo(prefijo)
    return f"{nombre_normalizado}_{prefijo_normalizado}.pdf"


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    """Renderiza la aplicación web principal (3 folios/expedientes)."""
    return templates.TemplateResponse(request=request, name="index.html")


import logging
logger = logging.getLogger(__name__)

@app.post("/api/declaracion-jurada")
def api_declaracion_jurada(
    ap_paterno: str = Form(...),
    ap_materno: str = Form(...),
    nombres: str = Form(...),
    dni: str = Form(...),
    domicilio: str = Form(...),
    distrito: str = Form(...),
    telefono: Optional[str] = Form(""),
    email: str = Form(...),
    condicion: str = Form(...),
    facultad: str = Form(...),
    fecha: str = Form(...),
    firma: UploadFile = File(...)
):
    """Genera la Declaración Jurada oficial UNMSM en formato PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        firma_ext = os.path.splitext(firma.filename)[1] or ".png"
        firma_path = os.path.join(tmpdir, f"firma{firma_ext}")
        with open(firma_path, "wb") as buffer:
            shutil.copyfileobj(firma.file, buffer)

        logo_path = os.path.join(BASE_DIR, "assets", "logofdcp.png")
        if not os.path.exists(logo_path):
            logo_path = None

        datos = {
            "ap_paterno": ap_paterno,
            "ap_materno": ap_materno,
            "nombres": nombres,
            "dni": dni,
            "domicilio": domicilio,
            "distrito": distrito,
            "telefono": telefono,
            "email": email,
            "condicion": condicion,
            "facultad": facultad,
            "fecha": fecha,
            "firma_path": firma_path
        }

        nombre_archivo = _nombre_archivo_usuario(
            "declaracion_jurada", nombres, ap_paterno, ap_materno
        )
        output_pdf_path = os.path.join(tmpdir, nombre_archivo)
        try:
            generar_declaracion_jurada(datos, output_pdf_path, logo_path=logo_path)
            with open(output_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            headers = {"Content-Disposition": f"attachment; filename={nombre_archivo}"}
            return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        except Exception as e:
            logger.error("Error al generar la Declaración Jurada", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al generar la Declaración Jurada: {str(e)}")


@app.post("/api/reporte-asistencia")
def api_reporte_asistencia(
    ap_paterno: str = Form(""),
    ap_materno: str = Form(""),
    nombres: str = Form(""),
    documento: UploadFile = File(...),
    firma: UploadFile = File(...)
):
    """Estampa la firma en el Reporte de Asistencia (.pdf o .docx) y devuelve PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_ext = os.path.splitext(documento.filename)[1].lower()
        if doc_ext not in [".pdf", ".docx"]:
            raise HTTPException(status_code=400, detail="Formato de documento no soportado. Debe ser .pdf o .docx")

        doc_path = os.path.join(tmpdir, f"documento_asistencia{doc_ext}")
        with open(doc_path, "wb") as buffer:
            shutil.copyfileobj(documento.file, buffer)

        firma_ext = os.path.splitext(firma.filename)[1] or ".png"
        firma_path = os.path.join(tmpdir, f"firma{firma_ext}")
        with open(firma_path, "wb") as buffer:
            shutil.copyfileobj(firma.file, buffer)

        nombre_extraido = _extraer_nombre_desde_documento(doc_path)
        nombre_persona = " ".join(str(parte).strip() for parte in (ap_paterno, ap_materno, nombres) if str(parte).strip())

        if nombre_persona:
            nombre_archivo = _nombre_archivo_usuario("reporte_asistencia", nombres, ap_paterno, ap_materno)
        else:
            nombre_archivo = f"{nombre_extraido}_reporte_asistencia.pdf"

        output_pdf_path = os.path.join(tmpdir, nombre_archivo)
        try:
            DocumentSigner.firmar_asistencia(doc_path, firma_path, output_pdf_path)
            with open(output_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            headers = {"Content-Disposition": f"attachment; filename={nombre_archivo}"}
            return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        except Exception as e:
            logger.error("Error al procesar el reporte de asistencia", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al procesar el reporte de asistencia: {str(e)}")


@app.post("/api/informe-actividades")
def api_informe_actividades(
    para_nombre: str = Form(...),
    para_cargo: Optional[str] = Form(""),
    de_nombre: str = Form(...),
    dni: str = Form(...),
    fecha_inicio: str = Form(...),
    fecha: str = Form(...),
    actividades: str = Form(""),
    evidencias: List[UploadFile] = File(default=[]),
    firma: UploadFile = File(...)
):
    """Genera el Informe de Actividades en PDF con evidencias fotográficas adjuntas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        firma_ext = os.path.splitext(firma.filename)[1] or ".png"
        firma_path = os.path.join(tmpdir, f"firma{firma_ext}")
        with open(firma_path, "wb") as buffer:
            shutil.copyfileobj(firma.file, buffer)

        evidencias_paths = []
        for i, ev_file in enumerate(evidencias):
            if not ev_file.filename:
                continue
            ev_ext = os.path.splitext(ev_file.filename)[1] or ".jpg"
            ev_path = os.path.join(tmpdir, f"evidencia_{i}{ev_ext}")
            with open(ev_path, "wb") as buffer:
                shutil.copyfileobj(ev_file.file, buffer)
            evidencias_paths.append(ev_path)

        datos = {
            "para_nombre": para_nombre,
            "para_cargo": para_cargo,
            "de_nombre": de_nombre,
            "dni": dni,
            "fecha_inicio": fecha_inicio,
            "fecha": fecha,
            "actividades": actividades,
            "evidencias": evidencias_paths,
            "firma_path": firma_path
        }

        nombre_archivo = _nombre_archivo_usuario("informe_actividades", nombre_completo=de_nombre)
        output_pdf_path = os.path.join(tmpdir, nombre_archivo)
        try:
            generar_informe_actividades(datos, output_pdf_path)
            with open(output_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            headers = {"Content-Disposition": f"attachment; filename={nombre_archivo}"}
            return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        except Exception as e:
            logger.error("Error al generar el Informe de Actividades", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al generar el Informe de Actividades: {str(e)}")
