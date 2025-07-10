# utils.py
from PyQt6.QtWidgets import QMessageBox
import json
import csv
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Попробуем зарегистрировать шрифт для PDF
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    PDF_FONT = 'Arial'
except Exception:
    PDF_FONT = 'Helvetica'

def validate_numeric(widget, min_val, max_val, percent=False):
    try:
        val = float(widget.text()) / 100 if percent else float(widget.text())
        if not (min_val < val < max_val):
            widget.setStyleSheet("border: 2px solid red;")
            return False
        else:
            widget.setStyleSheet("")
            return True
    except ValueError:
        widget.setStyleSheet("border: 2px solid red;")
        return False

def save_session_data(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_session_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def export_pdf(html, filepath):
    c = pdfcanvas.Canvas(filepath, pagesize=letter)
    c.setFont(PDF_FONT, 10)
    width, height = letter
    text = c.beginText(40, height - 40)
    text.setLeading(12)
    for line in html.strip().split('\n'):
        text.textLine(line)
    c.drawText(text)
    c.save()

def export_excel(sections, filepath):
    with pd.ExcelWriter(filepath) as writer:
        for name, lines in sections.items():
            rows = [line.strip().split(":") for line in lines if ":" in line]
            df = pd.DataFrame(rows, columns=["Metric", "Value"])
            df.to_excel(writer, sheet_name=name[:31], index=False)

def export_csv(sections, filepath):
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        for name, lines in sections.items():
            w.writerow([name])
            for line in lines:
                if ':' in line:
                    metric, value = [p.strip() for p in line.split(':', 1)]
                    w.writerow([metric, value])
            w.writerow([])

def show_error(parent, message):
    QMessageBox.critical(parent, "Ошибка", message)
