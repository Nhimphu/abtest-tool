import json
import csv
from typing import Any, Dict, Iterable, List

"""Utility helpers for exporting results and simple data processing."""


def export_pdf(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    """Export results to a notebook file instead of a PDF."""
    if filepath.lower().endswith(".pdf"):
        filepath = filepath[:-4] + ".ipynb"
    export_notebook(sections, filepath)


def export_excel(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    """Export results to a Markdown file instead of Excel."""
    if filepath.lower().endswith(('.xls', '.xlsx')):
        filepath = filepath.rsplit('.', 1)[0] + '.md'
    export_markdown(sections, filepath)


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
