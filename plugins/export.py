"""Optional heavy export helpers using external libraries."""
from typing import Dict, Iterable


def export_pdf(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    """Export results to a PDF using ``reportlab``."""
    try:
        from reportlab.pdfgen import canvas  # type: ignore
    except Exception as e:  # pragma: no cover - optional dependency
        raise ImportError("reportlab is required for PDF export") from e

    c = canvas.Canvas(filepath)
    y = 800
    for name, lines in sections.items():
        c.drawString(40, y, name)
        y -= 20
        for line in lines:
            c.drawString(60, y, str(line))
            y -= 15
        y -= 10
    c.save()


def export_excel(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    """Export results to an Excel file using ``pandas``."""
    try:
        import pandas as pd  # type: ignore
    except Exception as e:  # pragma: no cover - optional dependency
        raise ImportError("pandas is required for Excel export") from e

    rows = []
    for name, lines in sections.items():
        rows.append((name, ""))
        for line in lines:
            if ':' in line:
                metric, value = [p.strip() for p in line.split(':', 1)]
                rows.append((metric, value))
        rows.append(("", ""))

    df = pd.DataFrame(rows, columns=["Metric", "Value"])
    df.to_excel(filepath, index=False, header=False)
