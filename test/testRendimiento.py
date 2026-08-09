"""
test_rendimiento.py
Corre el flujo real de firmar_asistencia() midiendo RAM en cada etapa
y guarda todo en un log CSV, para tener datos reales (no estimados)
y decidir si el free tier de Render (512 MB RAM) es viable.

Uso:
    1) Primero generar las muestras de prueba (si no tenés documentos reales a mano):
         python generar_muestras.py

    2) Correr las pruebas:
         python test_rendimiento.py

    3) (Opcional) Usar tus propios archivos reales en vez de las muestras sintéticas:
         python test_rendimiento.py --doc "ruta/a/tu_asistencia.docx" --firma "ruta/a/tu_firma.png"
         python test_rendimiento.py --doc "ruta/a/tu_asistencia.pdf"  --firma "ruta/a/tu_firma.png"

Salida:
    - Log legible en consola con cada paso y su consumo de RAM.
    - Archivo CSV acumulativo en logs/rendimiento.csv (cada corrida agrega una fila),
      para poder comparar varias corridas / varios documentos a lo largo del tiempo.
"""

import argparse
import csv
import gc
import os
import sys
import time
from datetime import datetime

import psutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(os.path.dirname(BASE_DIR), "src")
sys.path.insert(0, SRC_DIR)

LOGS_DIR = os.path.join(BASE_DIR, "logs")
CSV_PATH = os.path.join(LOGS_DIR, "rendimiento.csv")

proceso = psutil.Process(os.getpid())


def ram_mb() -> float:
    """RAM real (RSS) usada por este proceso, en MB."""
    return proceso.memory_info().rss / (1024 * 1024)


class Medidor:
    """Acumula mediciones de (etapa, ram_mb, delta_mb, tiempo_seg) para el reporte final."""

    def __init__(self):
        self.filas = []
        self.ram_anterior = ram_mb()
        self.t_inicio_global = time.time()

    def marcar(self, etapa: str):
        ram_actual = ram_mb()
        delta = ram_actual - self.ram_anterior
        t_transcurrido = time.time() - self.t_inicio_global
        self.filas.append({
            "etapa": etapa,
            "ram_mb": round(ram_actual, 1),
            "delta_mb": round(delta, 1),
            "tiempo_acumulado_seg": round(t_transcurrido, 2),
        })
        signo = "+" if delta >= 0 else ""
        print(f"[{t_transcurrido:6.2f}s] {etapa:<45} RAM: {ram_actual:7.1f} MB  ({signo}{delta:.1f} MB)")
        self.ram_anterior = ram_actual

    def guardar_csv(self, meta: dict):
        os.makedirs(LOGS_DIR, exist_ok=True)
        existe = os.path.exists(CSV_PATH)
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not existe:
                writer.writerow([
                    "timestamp", "corrida_id", "so", "python_version",
                    "doc_entrada", "etapa", "ram_mb", "delta_mb", "tiempo_acumulado_seg"
                ])
            for fila in self.filas:
                writer.writerow([
                    meta["timestamp"], meta["corrida_id"], meta["so"], meta["python_version"],
                    meta["doc_entrada"], fila["etapa"], fila["ram_mb"],
                    fila["delta_mb"], fila["tiempo_acumulado_seg"],
                ])


def main():
    parser = argparse.ArgumentParser(description="Mide RAM/tiempo del flujo de firmado de documentos.")
    parser.add_argument("--doc", default=None, help="Ruta al .docx o .pdf de asistencia a firmar")
    parser.add_argument("--firma", default=None, help="Ruta a la imagen de firma (.png/.jpg)")
    args = parser.parse_args()

    muestras_dir = os.path.join(BASE_DIR, "muestras")
    doc_entrada = args.doc or os.path.join(muestras_dir, "asistencia_prueba.pdf")
    firma = args.firma or os.path.join(muestras_dir, "firma_prueba.png")

    if not os.path.exists(doc_entrada) or not os.path.exists(firma):
        print("⚠️  No se encontraron los archivos de entrada.")
        print(f"    Documento: {doc_entrada} (existe: {os.path.exists(doc_entrada)})")
        print(f"    Firma:     {firma} (existe: {os.path.exists(firma)})")
        print("\nSi no tenés documentos reales a mano, generá muestras primero con:")
        print("    python generar_muestras.py")
        sys.exit(1)

    salida_pdf = os.path.join(BASE_DIR, "salida_firmada.pdf")

    med = Medidor()
    med.marcar("Inicio (Python + intérprete cargado)")

    # --- Import de librerías, una por una, midiendo el costo de cada una ---
    import fitz  # noqa: F401  (PyMuPDF)
    med.marcar("import fitz (PyMuPDF)")

    import pypdf  # noqa: F401
    med.marcar("import pypdf")

    from reportlab.pdfgen import canvas  # noqa: F401
    med.marcar("import reportlab")

    import docx  # noqa: F401
    med.marcar("import python-docx")

    from PIL import Image  # noqa: F401
    med.marcar("import Pillow")

    # Importamos el módulo del proyecto DESPUÉS de medir las librerías sueltas,
    # así vemos si el import del propio módulo agrega algo extra.
    from docx_handler import DocumentSigner
    med.marcar("import docx_handler (nuestro módulo)")

    med.marcar("Baseline final antes de procesar (esto es lo que pesa 'en idle')")

    # --- Procesamiento real ---
    t0 = time.time()
    try:
        resultado = DocumentSigner.firmar_asistencia(doc_entrada, firma, salida_pdf)
        exito = True
    except Exception as e:
        print(f"\n❌ ERROR durante el procesamiento: {e}")
        resultado = None
        exito = False
    t1 = time.time()

    med.marcar(f"Después de firmar_asistencia() [{t1 - t0:.2f}s]")

    gc.collect()
    med.marcar("Después de gc.collect()")

    # --- Reporte final ---
    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    pico_ram = max(f["ram_mb"] for f in med.filas)
    print(f"Documento de entrada:     {doc_entrada}")
    print(f"Éxito:                    {'✅ Sí' if exito else '❌ No'}")
    if exito:
        print(f"Archivo de salida:        {resultado}")
    print(f"Pico de RAM alcanzado:    {pico_ram:.1f} MB")
    print(f"Margen sobre free tier:   {512 - pico_ram:.1f} MB libres (de 512 MB totales)")
    if pico_ram > 512:
        print("🚨 SUPERA el límite del free tier de Render (512 MB). Necesitarías un plan pago.")
    elif pico_ram > 400:
        print("⚠️  Cerca del límite del free tier. Riesgoso bajo carga o con documentos más grandes.")
    else:
        print("✅ Dentro de un margen razonable para el free tier de Render.")
    print(f"Tiempo total de procesamiento: {t1 - t0:.2f} segundos")

    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "corrida_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "so": sys.platform,
        "python_version": sys.version.split()[0],
        "doc_entrada": os.path.basename(doc_entrada),
    }
    med.guardar_csv(meta)
    print(f"\n📄 Resultados agregados al log: {CSV_PATH}")


if __name__ == "__main__":
    main()