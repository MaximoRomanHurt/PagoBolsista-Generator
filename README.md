# 🎓 Generador de Documentos de Pago para Bolsistas — UNMSM

Sistema de escritorio para generar y firmar los **3 documentos requeridos para el cobro de bolsistas** en la Universidad Nacional Mayor de San Marcos (UNMSM).

---

## 📋 Descripción

Los bolsistas de la UNMSM deben presentar mensualmente tres documentos obligatorios para el trámite de su estipendio/pago:
1. **Declaración Jurada de No Pertenecer a Órganos de Gobierno** (Ley N° 30220).
2. **Reporte / Consulta de Asistencias** (Documento oficial emitido con la estampa de firma).
3. **Informe de Actividades** (Con relación de tareas y evidencias fotográficas adjuntas).

Esta aplicación simplifica el proceso ofreciendo un menú interactivo para elegir el documento, completar los formularios con autollenado de datos personales y generar los archivos PDF o DOCX firmados en segundos.

---

## 🛠️ Los 3 Documentos Soportados

| Documento | Descripción | Acción / Salida |
|---|---|---|
| 📜 **Declaración Jurada** | Cumplimiento del Art. 104º de la Ley N° 30220. | Formulario con datos personales, fecha y firma -> **PDF** |
| 📅 **Reporte de Asistencia** | Documento de asistencias otorgado por la facultad o dependencia. | Carga de archivo (DOCX/PDF) + Firma -> **Salida en PDF** |
| 📊 **Informe de Actividades** | Detalle de labores del mes con soporte fotográfico. | Formulario de destinatario, tareas, fotos y firma -> **PDF de 2+ páginas** |

---

## ✨ Características Destacadas y Novedades

> [!NOTE]
> **Detección Dinámica de Firmas en Reporte de Asistencias (Visión por Computadora):**
> El sistema incluye un motor basado en **Visión por Computadora (OpenCV) y Extracción de Tablas (PyMuPDF)** que detecta automáticamente las celdas de la columna "FIRMA" sin importar la cantidad variable de días/filas ni el formato del PDF de cada facultad. Las firmas se estampan perfectamente centradas en cada celda sin modificar las dimensiones del documento ni pisar los textos de resumen del pie de página.

---

## 🛠️ Errores Resueltos y Correcciones (Bug Fixes)

> [!TIP]
> **Bug de Estampado y Desborde de Firmas en Asistencias (RESUELTO ✅):**
> - **Problema previo:** Las firmas se colocaban usando posiciones y cantidad de filas estáticas (12 filas fijas), lo que provocaba que se desalinearan, se saltaran la primera fila y se desbordaran estampándose sobre las notas de resumen al pie del reporte (`Total a pagar`, `Precio por turno`, etc.).
> - **Solución implementada:** Se reestructuró `src/docx_handler.py` añadiendo delimitación estricta de bordes de tabla y centrado geométrico inteligente. Ahora se identifican únicamente las filas reales de datos, omitiendo automáticamente las celdas de pie de página/totales y centrando la firma en cada recuadro.
> - **Estado:** Totalmente corregido y funcional para cualquier plantilla `.pdf` o `.docx`.

---



## 🖥️ Flujo de Uso

1. Al abrir la aplicación se presenta una **pantalla inicial con 3 tarjetas**.
2. Al hacer clic en un documento, se abre el formulario correspondiente:
   - En **Declaración Jurada**: Ingresa tus datos (DNI, domicilio, correo, etc.), fecha y selecciona la foto de tu firma. Tus datos se guardarán automáticamente para autollenados futuros.
   - En **Reporte de Asistencias**: Selecciona el archivo `.docx` o `.pdf` recibido y la foto de tu firma para exportar a PDF.
   - En **Informe de Actividades**: Ingresa el destinatario, las actividades realizadas, adjunta las fotos de evidencia y tu firma.
3. Haz clic en **Generar** o **Estampar Firma**. Los archivos listos se guardarán automáticamente en la carpeta `output/`.
4. En cualquier momento puedes pulsar **`← Volver`** para regresar al menú principal.

---

## 📁 Estructura del Proyecto

```
cv_generator/
├── src/
│   ├── main.py                     # Punto de entrada y navegación GUI
│   ├── pdf_generator.py            # Generador ReportLab para Decl. Jurada e Informe
│   ├── docx_handler.py             # Estampador de firmas en DOCX y PDF de asistencias
│   ├── user_profile.py             # Gestor de persistencia de datos (Autollenado)
│   ├── controllers/
│   │   └── bolsista_controller.py  # Controlador de validaciones y archivos
│   └── ui/
│       ├── config.py               # Colores y constantes
│       ├── utils.py                # Utilidades de centrado y texto
│       ├── view_seleccion.py       # Pantalla inicial (3 tarjetas)
│       ├── view_declaracion.py     # Vista de Declaración Jurada
│       ├── view_asistencia.py      # Vista de Asistencia
│       └── view_informe.py         # Vista de Informe de Actividades
├── assets/                         # Escudos y logos institucionales
├── output/                         # Documentos firmados/generados (PDF/DOCX)
├── user_profile.json               # Datos del perfil guardado para autollenado
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalación

### Windows (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

---

## ▶️ Ejecución

Ejecuta la aplicación desde el entorno virtual:

```powershell
python src/main.py
```