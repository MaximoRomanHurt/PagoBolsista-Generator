"""
app/main.py
Servidor FastAPI para la versión WEB del Generador de Documentos de Pago — UNMSM.
"""

import os
import sys
import tempfile
import shutil
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

        output_pdf_path = os.path.join(tmpdir, "declaracion_jurada.pdf")
        try:
            generar_declaracion_jurada(datos, output_pdf_path, logo_path=logo_path)
            with open(output_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            headers = {"Content-Disposition": "attachment; filename=declaracion_jurada.pdf"}
            return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        except Exception as e:
            logger.error("Error al generar la Declaración Jurada", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al generar la Declaración Jurada: {str(e)}")


@app.post("/api/reporte-asistencia")
def api_reporte_asistencia(
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

        output_pdf_path = os.path.join(tmpdir, "reporte_asistencia_firmado.pdf")
        try:
            DocumentSigner.firmar_asistencia(doc_path, firma_path, output_pdf_path)
            with open(output_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            headers = {"Content-Disposition": "attachment; filename=reporte_asistencia_firmado.pdf"}
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

        output_pdf_path = os.path.join(tmpdir, "informe_actividades.pdf")
        try:
            generar_informe_actividades(datos, output_pdf_path)
            with open(output_pdf_path, "rb") as f:
                pdf_bytes = f.read()

            headers = {"Content-Disposition": "attachment; filename=informe_actividades.pdf"}
            return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        except Exception as e:
            logger.error("Error al generar el Informe de Actividades", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al generar el Informe de Actividades: {str(e)}")
