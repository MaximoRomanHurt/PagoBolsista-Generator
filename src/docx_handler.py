"""
docx_handler.py
Estampador de firmas en reportes de asistencia (DOCX / PDF).
Garantiza que la salida sea SIEMPRE un archivo PDF y que la firma encaje
exactamente dentro de las celdas sin alterar las dimensiones ni la estructura original.
"""

import os
import io
from PIL import Image as PILImage

try:
    import docx
    from docx.shared import Inches, Pt
except ImportError:
    docx = None

try:
    import pypdf
    from reportlab.pdfgen import canvas
except ImportError:
    pypdf = None


class DocumentSigner:
    """Inserta la firma en archivos de asistencia y exporta SIEMPRE en formato PDF."""

    @staticmethod
    def _convertir_docx_a_pdf(ruta_docx: str, ruta_pdf_salida: str) -> bool:
        """Intenta convertir un archivo DOCX a PDF usando win32com (MS Word) o docx2pdf."""
        # 1. Intentar win32com (MS Word oficial en Windows)
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc_obj = word.Documents.Open(os.path.abspath(ruta_docx))
            doc_obj.SaveAs(os.path.abspath(ruta_pdf_salida), FileFormat=17) # 17 = wdFormatPDF
            doc_obj.Close()
            word.Quit()
            if os.path.exists(ruta_pdf_salida):
                return True
        except Exception:
            pass

        # 2. Intentar librería docx2pdf
        try:
            from docx2pdf import convert
            convert(ruta_docx, ruta_pdf_salida)
            if os.path.exists(ruta_pdf_salida):
                return True
        except Exception:
            pass

        return False

    @classmethod
    def firmar_asistencia(cls, ruta_doc: str, ruta_firma: str, ruta_pdf_final: str) -> str:
        """
        Recibe un archivo .docx o .pdf de asistencia y una firma.
        Inserta la firma sin alterar el tamaño de celdas y retorna la ruta del PDF firmado final.
        """
        if not os.path.exists(ruta_doc):
            raise FileNotFoundError(f"No se encontró el archivo de asistencia: {ruta_doc}")
        if not os.path.exists(ruta_firma):
            raise FileNotFoundError(f"No se encontró la imagen de la firma: {ruta_firma}")

        ext = os.path.splitext(ruta_doc)[1].lower()

        if ext == ".docx":
            if not docx:
                raise ImportError("La librería 'python-docx' no está instalada.")

            doc = docx.Document(ruta_doc)
            firmas_insertadas = 0

            for table in doc.tables:
                col_indices = []
                if len(table.rows) > 0:
                    for idx, cell in enumerate(table.rows[0].cells):
                        if "FIRMA" in cell.text.upper():
                            col_indices.append(idx)

                for row in table.rows[1:]:
                    for col_idx in col_indices:
                        if col_idx < len(row.cells):
                            cell = row.cells[col_idx]
                            cell.text = "" # Limpiar texto manteniendo formato
                            p = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
                            p.paragraph_format.space_before = Pt(0)
                            p.paragraph_format.space_after = Pt(0)
                            run = p.add_run()
                            # Firma de tamaño exacto que encaja en la celda
                            run.add_picture(ruta_firma, width=Inches(0.95), height=Inches(0.28))
                            firmas_insertadas += 1

            if firmas_insertadas == 0:
                for p in doc.paragraphs:
                    if "FIRMA" in p.text.upper():
                        p.text = ""
                        p.paragraph_format.space_before = Pt(0)
                        p.paragraph_format.space_after = Pt(0)
                        run = p.add_run()
                        run.add_picture(ruta_firma, width=Inches(1.2), height=Inches(0.35))

            # Guardar temporalmente el docx firmado
            temp_docx = ruta_pdf_final.replace(".pdf", "_temp.docx")
            doc.save(temp_docx)

            # Convertir a PDF (Salida obligatoria en PDF)
            exito_pdf = cls._convertir_docx_a_pdf(temp_docx, ruta_pdf_final)

            # Limpiar temporal
            if os.path.exists(temp_docx):
                try: os.remove(temp_docx)
                except Exception: pass

            if exito_pdf:
                return ruta_pdf_final
            else:
                raise RuntimeError("No se pudo convertir el DOCX a PDF. Instala MS Word o 'docx2pdf'.")

        elif ext == ".pdf":
            if not pypdf:
                raise ImportError("La librería 'pypdf' no está instalada.")

            reader = pypdf.PdfReader(ruta_doc)
            writer = pypdf.PdfWriter()

            packet = io.BytesIO()
            can = canvas.Canvas(packet)
            
            page0 = reader.pages[0]
            w = float(page0.mediabox.width)
            h = float(page0.mediabox.height)

            # Posicionar firmas dentro de las casillas de la tabla (sin desbordar)
            y_starts = [h * 0.82 - (i * 26.5) for i in range(12)]
            for y_pos in y_starts:
                if y_pos > 150:
                    can.drawImage(ruta_firma, w * 0.31, y_pos + 2, width=58, height=18, mask='auto', preserveAspectRatio=True)
                    can.drawImage(ruta_firma, w * 0.57, y_pos + 2, width=58, height=18, mask='auto', preserveAspectRatio=True)
            
            can.save()
            packet.seek(0)

            overlay_pdf = pypdf.PdfReader(packet)
            overlay_page = overlay_pdf.pages[0]

            for i, page in enumerate(reader.pages):
                if i == 0:
                    page.merge_page(overlay_page)
                writer.add_page(page)

            with open(ruta_pdf_final, "wb") as f_out:
                writer.write(f_out)

            return ruta_pdf_final
        else:
            raise ValueError("Formato de entrada no soportado. Debe ser .docx o .pdf")
