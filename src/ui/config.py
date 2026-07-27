"""
ui/config.py
Configuración centralizada: colores, rutas, constantes UI para la App de Bolsistas UNMSM.
"""

import os

# ── Paleta de Colores ────────────────────────────────────────────────────────
COLOR_PRIMARIO   = "#4B0002"   # guinda institucional UNMSM
COLOR_HOVER      = "#6B0003"
COLOR_SEGUNDARIO = "#D4AF37"   # dorado institucional
COLOR_ALERTA     = "#B22222"
COLOR_EXITO      = "#2E7D32"
COLOR_FONDO      = "#F8F9FA"
COLOR_TARJETA    = "#FFFFFF"
COLOR_TEXTO      = "#2C2C2C"

# ── Rutas ────────────────────────────────────────────────────────────────────
SRC_DIR          = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR      = os.path.dirname(SRC_DIR)
LOGO_PATH        = os.path.join(PROJECT_DIR, "assets", "logofdcp.png")
OUTPUT_DIR       = os.path.join(PROJECT_DIR, "output")

# ── Dimensiones de la ventana ────────────────────────────────────────────────
WINDOW_WIDTH     = 850
WINDOW_HEIGHT    = 680

# ── Tipos de archivo ────────────────────────────────────────────────────────
IMAGE_FILETYPES  = [("Imágenes", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")]
DOCX_PDF_FILETYPES = [("Documentos (DOCX, PDF)", "*.docx *.pdf"), ("Word DOCX", "*.docx"), ("PDF", "*.pdf"), ("Todos", "*.*")]
