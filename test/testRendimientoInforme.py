"""
test_rendimiento_informe.py
Mide RAM/tiempo del flujo de generar_informe_actividades() con N imágenes
de evidencia, para saber cuánto consume esta función específica.

Uso:
    python test_rendimiento_informe.py --imagenes "C:\\ruta\\a\\carpeta_con_fotos" --firma "C:\\ruta\\a\\firma.png"

    Por defecto usa hasta 20 imágenes de la carpeta indicada (las primeras
    20 que encuentre, ordenadas alfabéticamente). Podés cambiar el límite
    con --max, por ejemplo --max 4 para probar solo con 4.

Salida:
    - Log en consola con RAM en cada etapa.
    - Fila agregada a logs/rendimiento_informe.csv para poder comparar
      corridas con distinta cantidad de imágenes a lo largo del tiempo.
"""

import argparse
import csv
import gc
import glob
import os
import sys
import time
from datetime import datetime

import psutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(os.path.dirname(BASE_DIR), "src")
sys.path.insert(0, SRC_DIR)

LOGS_DIR = os.path.join(BASE_DIR, "logs")
CSV_PATH = os.path.join(LOGS_DIR, "rendimiento_informe.csv")

EXTENSIONES_VALIDAS = (".jpg", ".jpeg", ".png", ".webp")

proceso = psutil.Process(os.getpid())


def ram_mb() -> float:
    return proceso.memory_info().rss / (1024 * 1024)


class Medidor:
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
        print(f"[{t_transcurrido:6.2f}s] {etapa:<50} RAM: {ram_actual:7.1f} MB  ({signo}{delta:.1f} MB)")
        self.ram_anterior = ram_actual

    def guardar_csv(self, meta: dict):
        os.makedirs(LOGS_DIR, exist_ok=True)
        existe = os.path.exists(CSV_PATH)
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not existe:
                writer.writerow([
                    "timestamp", "corrida_id", "so", "python_version",
                    "num_imagenes", "peso_total_imagenes_mb", "etapa",
                    "ram_mb", "delta_mb", "tiempo_acumulado_seg"
                ])
            for fila in self.filas:
                writer.writerow([
                    meta["timestamp"], meta["corrida_id"], meta["so"], meta["python_version"],
                    meta["num_imagenes"], meta["peso_total_imagenes_mb"], fila["etapa"],
                    fila["ram_mb"], fila["delta_mb"], fila["tiempo_acumulado_seg"],
                ])


def main():
    parser = argparse.ArgumentParser(description="Mide RAM/tiempo de generar_informe_actividades().")
    parser.add_argument("--imagenes", required=True, help="Carpeta con las imágenes de evidencia")
    parser.add_argument("--firma", required=True, help="Ruta a la imagen de firma")
    parser.add_argument("--max", type=int, default=20, help="Máximo de imágenes a usar (default 20)")
    args = parser.parse_args()

    if not os.path.isdir(args.imagenes):
        print(f"⚠️  La carpeta de imágenes no existe: {args.imagenes}")
        sys.exit(1)
    if not os.path.exists(args.firma):
        print(f"⚠️  No se encontró la imagen de firma: {args.firma}")
        sys.exit(1)

    rutas_imagenes = sorted([
        f for f in glob.glob(os.path.join(args.imagenes, "*"))
        if f.lower().endswith(EXTENSIONES_VALIDAS)
    ])[: args.max]

    if not rutas_imagenes:
        print(f"⚠️  No se encontraron imágenes ({', '.join(EXTENSIONES_VALIDAS)}) en: {args.imagenes}")
        sys.exit(1)

    peso_total_mb = sum(os.path.getsize(p) for p in rutas_imagenes) / (1024 * 1024)

    print(f"📸 Usando {len(rutas_imagenes)} imágenes (peso total sin comprimir: {peso_total_mb:.2f} MB)")
    for p in rutas_imagenes:
        print(f"   - {os.path.basename(p)} ({os.path.getsize(p) / 1024:.0f} KB)")
    print()

    salida_pdf = os.path.join(BASE_DIR, "informe_prueba_generado.pdf")

    med = Medidor()
    med.marcar("Inicio (Python + intérprete cargado)")

    from pdf_generator import generar_informe_actividades
    med.marcar("import pdf_generator (incluye reportlab, PIL)")

    med.marcar("Baseline final antes de procesar")

    datos = {
        "anio": "2026",
        "para_nombre": "Oficina de Personal",
        "para_cargo": "UNMSM",
        "de_nombre": "Estudiante de Prueba",
        "asunto": "Informe de actividades - prueba de rendimiento",
        "fecha": "Lima, 08 de Agosto de 2026",
        "fecha_inicio": "01 de Agosto",
        "dni": "12345678",
        "actividades": [
            "Apoyo en la organización de archivos administrativos.",
            "Elaboración de reportes mensuales de seguimiento.",
            "Coordinación con la oficina de personal para trámites de bolsistas.",
        ],
        "evidencias": rutas_imagenes,
        "firma_path": args.firma,
    }

    t0 = time.time()
    try:
        resultado = generar_informe_actividades(datos, salida_pdf)
        exito = True
    except Exception as e:
        print(f"\n❌ ERROR durante el procesamiento: {e}")
        resultado = None
        exito = False
    t1 = time.time()

    med.marcar(f"Después de generar_informe_actividades() [{t1 - t0:.2f}s]")

    gc.collect()
    med.marcar("Después de gc.collect()")

    print("\n" + "=" * 70)
    print("RESUMEN")
    print("=" * 70)
    pico_ram = max(f["ram_mb"] for f in med.filas)
    print(f"Cantidad de imágenes:      {len(rutas_imagenes)}")
    print(f"Peso original (sin comp.): {peso_total_mb:.2f} MB")
    print(f"Éxito:                     {'✅ Sí' if exito else '❌ No'}")
    if exito:
        peso_pdf_mb = os.path.getsize(resultado) / (1024 * 1024)
        print(f"Archivo de salida:         {resultado}")
        print(f"Peso del PDF final:        {peso_pdf_mb:.2f} MB")
    print(f"Pico de RAM alcanzado:     {pico_ram:.1f} MB")
    print(f"Margen sobre free tier:    {512 - pico_ram:.1f} MB libres (de 512 MB totales)")
    if pico_ram > 512:
        print("🚨 SUPERA el límite del free tier de Render (512 MB). Necesitarías un plan pago.")
    elif pico_ram > 400:
        print("⚠️  Cerca del límite del free tier. Riesgoso bajo carga o con más imágenes.")
    else:
        print("✅ Dentro de un margen razonable para el free tier de Render.")
    print(f"Tiempo total de procesamiento: {t1 - t0:.2f} segundos")

    meta = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "corrida_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "so": sys.platform,
        "python_version": sys.version.split()[0],
        "num_imagenes": len(rutas_imagenes),
        "peso_total_imagenes_mb": round(peso_total_mb, 2),
    }
    med.guardar_csv(meta)
    print(f"\n📄 Resultados agregados al log: {CSV_PATH}")


if __name__ == "__main__":
    main()