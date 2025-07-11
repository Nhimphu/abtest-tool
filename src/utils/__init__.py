import json
import csv
from typing import Any, Dict, Iterable, List

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Try to register font for PDF export
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    PDF_FONT = 'Arial'
except Exception:  # pragma: no cover - optional
    PDF_FONT = 'Helvetica'


def export_pdf(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    """Export results following the notebook template into a PDF."""
    order = ["Описание", "Результаты", "Визуализации", "Интерпретация"]
    c = pdfcanvas.Canvas(filepath, pagesize=letter)
    c.setFont(PDF_FONT, 10)
    _, height = letter
    y = height - 40
    for name in order:
        lines = sections.get(name, [])
        c.drawString(40, y, name)
        y -= 14
        for line in lines:
            c.drawString(60, y, str(line))
            y -= 12
        y -= 10
    c.save()


def export_excel(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    with pd.ExcelWriter(filepath) as writer:
        for name, lines in sections.items():
            rows = [line.strip().split(":") for line in lines if ":" in line]
            df = pd.DataFrame(rows, columns=["Metric", "Value"])
            df.to_excel(writer, sheet_name=name[:31], index=False)


def export_csv(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        for name, lines in sections.items():
            w.writerow([name])
            for line in lines:
                if ':' in line:
                    metric, value = [p.strip() for p in line.split(':', 1)]
                    w.writerow([metric, value])
            w.writerow([])


def export_markdown(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        for name, lines in sections.items():
            f.write(f"## {name}\n")
            for line in lines:
                f.write(f"{line}\n")
            f.write("\n")


def export_notebook(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    """Export results following the notebook template."""
    order = ["Описание", "Результаты", "Визуализации", "Интерпретация"]
    cells = []
    for name in order:
        lines = sections.get(name, [])
        cell = {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"## {name}\n"] + [str(line) + "\n" for line in lines],
        }
        cells.append(cell)
    nb = {"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 2}
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)


def segment_data(records: List[Dict[str, Any]], **filters: Any) -> List[Dict[str, Any]]:
    """Return subset of records matching simple equality filters."""
    return [r for r in records if all(r.get(k) == v for k, v in filters.items())]


def compute_custom_metric(records: List[Dict[str, Any]], expression: str) -> float:
    """Safely evaluate simple metric expressions on ``records``."""
    import ast

    def _eval(node):
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            raise ValueError("Unsupported operator")
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.USub):
                return -_eval(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +_eval(node.operand)
            raise ValueError("Unsupported unary operator")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Invalid function call")
            name = node.func.id
            if name not in {"sum", "len"} or len(node.args) != 1:
                raise ValueError("Invalid function")
            arg = node.args[0]
            if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
                raise ValueError("Invalid argument")
            field = arg.value
            if name == "sum":
                return sum(float(r.get(field, 0)) for r in records)
            else:
                return len(records)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid constant")
        raise ValueError("Unsupported expression")

    tree = ast.parse(expression, mode="eval")
    return _eval(tree.body)
