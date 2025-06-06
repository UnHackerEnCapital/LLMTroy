import sys
import os
import hashlib
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QFileDialog, QVBoxLayout,
                             QLabel, QTextEdit, QHBoxLayout)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

class PDFInjector(QWidget):
    def __init__(self, ruta_logo):
        super().__init__()

        self.setWindowTitle("Inyector/Analizador de Prompts Ocultos")
        self.setGeometry(100, 100, 700, 550)
        self.setStyleSheet("background-color: black; color: white;")

        self.layout = QVBoxLayout()

        self.banner = QLabel()
        pixmap = QPixmap(ruta_logo)
        self.banner.setPixmap(pixmap.scaledToWidth(600, Qt.SmoothTransformation))
        self.banner.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.banner)

        header = QLabel("Inyector y Analizador de Prompts Ocultos")
        header.setFont(QFont("Courier", 14, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(header)

        self.label = QLabel("Seleccioná un documento PDF:")
        self.layout.addWidget(self.label)

        self.select_button = QPushButton("Cargar PDF")
        self.select_button.clicked.connect(self.load_pdf)
        self.layout.addWidget(self.select_button)

        self.prompt_label = QLabel("Código oculto detectado o a inyectar:")
        self.layout.addWidget(self.prompt_label)

        self.prompt_input = QTextEdit()
        self.layout.addWidget(self.prompt_input)

        button_layout = QHBoxLayout()
        self.inject_button = QPushButton("Inyectar Código")
        self.inject_button.clicked.connect(self.inject_code)
        button_layout.addWidget(self.inject_button)

        self.analyze_button = QPushButton("Analizar PDF y Mostrar Código Oculto")
        self.analyze_button.clicked.connect(self.extract_hidden_code)
        button_layout.addWidget(self.analyze_button)

        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

        self.pdf_path = None
        button_style = "background-color: #222; color: white; font-weight: bold;"
        self.select_button.setStyleSheet(button_style)
        self.inject_button.setStyleSheet(button_style)
        self.analyze_button.setStyleSheet(button_style)

    def load_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "Archivos PDF (*.pdf)")
        if path:
            self.pdf_path = path
            self.label.setText(f"PDF cargado: {os.path.basename(path)}")

    def extract_hidden_code(self):
        if not self.pdf_path:
            self.label.setText("⚠️ Primero cargá un archivo PDF.")
            return
        try:
            reader = PdfReader(self.pdf_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() or ""

            bloques = []
            bloque_actual = []

            for linea in full_text.splitlines():
                if any(etiqueta in linea for etiqueta in [
                    "[comentario_invisible]",
                    "[modulo_seguro_prompt]",
                    "[llm_restriccion]"
                ]) or ("os.system" in linea and not linea.strip().startswith("#")) or ("import os" in linea and not linea.strip().startswith("#")):
                    bloque_actual.append(linea.strip())
                elif bloque_actual:
                    bloques.append("\n".join(bloque_actual))
                    bloque_actual = []

            if bloque_actual:
                bloques.append("\n".join(bloque_actual))

            if bloques:
                self.prompt_input.setPlainText(bloques[-1])
                self.label.setText("✅ Código oculto más reciente recuperado del PDF.")
            else:
                self.prompt_input.setPlainText("")
                self.label.setText("⚠️ No se encontró código oculto.")
        except Exception as e:
            self.label.setText(f"❌ Error al analizar el PDF: {str(e)}")

    def inject_code(self):
        if not self.pdf_path:
            self.label.setText("⚠️ Primero cargá un archivo PDF.")
            return

        prompt = self.prompt_input.toPlainText()
        if not prompt.strip():
            self.label.setText("⚠️ El texto está vacío.")
            return

        try:
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.setFillColorRGB(1, 1, 1)
            textobject = c.beginText(10, 750)
            for line in prompt.strip().splitlines():
                textobject.textLine(line)
            c.drawText(textobject)
            c.save()
            buffer.seek(0)

            original = PdfReader(self.pdf_path)
            nuevo = PdfReader(buffer)
            writer = PdfWriter()

            full_text = ""
            for page in original.pages:
                full_text += page.extract_text() or ""

            bloques_ocultos = []
            bloque_actual = []

            for linea in full_text.splitlines():
                if any(etiqueta in linea for etiqueta in [
                    "[comentario_invisible]",
                    "[modulo_seguro_prompt]",
                    "[llm_restriccion]"
                ]) or ("os.system" in linea and not linea.strip().startswith("#")) or ("import os" in linea and not linea.strip().startswith("#")):
                    bloque_actual.append(linea.strip())
                elif bloque_actual:
                    bloques_ocultos.append("\n".join(bloque_actual))
                    bloque_actual = []
            if bloque_actual:
                bloques_ocultos.append("\n".join(bloque_actual))

            hashes_ocultos = [hashlib.sha256(b.encode()).hexdigest() for b in bloques_ocultos]

            for page in original.pages:
                text = page.extract_text() or ""
                contenido = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
                hash_pagina = hashlib.sha256(contenido.encode()).hexdigest()
                if hash_pagina in hashes_ocultos:
                    continue
                writer.add_page(page)

            writer.add_page(nuevo.pages[0])

            output_path, _ = QFileDialog.getSaveFileName(self, "Guardar PDF modificado", "output_sensorfernet.pdf", "PDF Files (*.pdf)")
            if output_path:
                with open(output_path, "wb") as f:
                    writer.write(f)
                self.label.setText(f"✅ Código oculto inyectado en: {os.path.basename(output_path)}")
        except Exception as e:
            self.label.setText(f"❌ Error al inyectar: {str(e)}")

# === MAIN ===
if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        ruta_icono = os.path.join(sys._MEIPASS, "icono.ico")
        ruta_logo = os.path.join(sys._MEIPASS, "logo.png")
    else:
        ruta_icono = "icono.ico"
        ruta_logo = "logo.png"

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ruta_icono))  # 🔥 ICONO GLOBAL PARA APP

    ventana = PDFInjector(ruta_logo)
    ventana.show()
    sys.exit(app.exec_())
