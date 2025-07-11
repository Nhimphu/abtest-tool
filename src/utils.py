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
    pdfmetrics.registerFont(TTFont("Arial", "arial.ttf"))
    PDF_FONT = "Arial"
except Exception:
    PDF_FONT = "Helvetica"


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


def export_pdf(data, filepath):
    """Export plain text or sectioned report to PDF."""
    c = pdfcanvas.Canvas(filepath, pagesize=letter)
    c.setFont(PDF_FONT, 10)
    width, height = letter
    y = height - 40

    if isinstance(data, dict):
        for name, lines in data.items():
            c.drawString(40, y, name)
            y -= 12
            for line in lines:
                c.drawString(60, y, str(line))
                y -= 12
                if y < 40:
                    c.showPage()
                    c.setFont(PDF_FONT, 10)
                    y = height - 40
            y -= 12
    else:
        for line in str(data).strip().split("\n"):
            c.drawString(40, y, line)
            y -= 12
            if y < 40:
                c.showPage()
                c.setFont(PDF_FONT, 10)
                y = height - 40

    c.save()


def export_excel(sections, filepath):
    with pd.ExcelWriter(filepath) as writer:
        for name, lines in sections.items():
            rows = [line.strip().split(":") for line in lines if ":" in line]
            df = pd.DataFrame(rows, columns=["Metric", "Value"])
            df.to_excel(writer, sheet_name=name[:31], index=False)


def export_csv(sections, filepath):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for name, lines in sections.items():
            w.writerow([name])
            for line in lines:
                if ":" in line:
                    metric, value = [p.strip() for p in line.split(":", 1)]
                    w.writerow([metric, value])
            w.writerow([])


def show_error(parent, message):
    QMessageBox.critical(parent, "Ошибка", message)


def export_markdown(sections, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        for name, lines in sections.items():
            f.write(f"## {name}\n")
            for line in lines:
                f.write(f"{line}\n")
            f.write("\n")


def export_notebook(sections, filepath):
    """Export results to a minimal Jupyter notebook file."""
    cells = []
    for name, lines in sections.items():
        cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"## {name}\n"] + [line + "\n" for line in lines],
        }
        cells.append(cell)
    nb = {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 2}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)
