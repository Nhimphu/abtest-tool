"""Optional heavy export helpers using external libraries."""
from typing import Any, Dict, Iterable, Set

from abtest_core.backends import get_backend

ABI_VERSION = "1.0"
name = "export"
version = "0.1"
capabilities: Set[str] = {"report"}

def export_pdf(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    """Export results to a PDF using ``reportlab``."""
    canvas = get_backend("reportlab.pdfgen.canvas")
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
    pd = get_backend("pandas")
    rows = []
    for name, lines in sections.items():
        rows.append((name, ""))
        for line in lines:
            if ":" in line:
                metric, value = [p.strip() for p in line.split(":", 1)]
                rows.append((metric, value))
        rows.append(("", ""))

    df = pd.DataFrame(rows, columns=["Metric", "Value"])
    df.to_excel(filepath, index=False, header=False)

def register(app: Any) -> None:  # pragma: no cover - nothing to do
    """Export plugin does not require registration."""
    return None

__all__ = ["export_pdf", "export_excel", "register"]
