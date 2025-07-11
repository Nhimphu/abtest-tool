import json
import csv
import copy
from typing import Any, Dict, Iterable, List

from .template import NB_TEMPLATE

from .safe_eval import safe_eval
import plugin_loader

"""Utility helpers for exporting results and simple data processing."""


def export_pdf(sections: Dict[str, Iterable[str]], filepath: str) -> None:
    """Render ``sections`` using the notebook template and save as ``.ipynb``.

    ``export_pdf`` is kept as a thin wrapper for backwards compatibility. It
    simply redirects to :func:`export_notebook` while adjusting the extension.
    """
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
    """Render ``sections`` according to :data:`NB_TEMPLATE`."""

    order = ["Description", "Results", "Visualizations", "Interpretation"]
    aliases = {
        "Описание": "Description",
        "Результаты": "Results",
        "Визуализации": "Visualizations",
        "Интерпретация": "Interpretation",
    }

    nb = copy.deepcopy(NB_TEMPLATE)
    for cell, key in zip(nb["cells"], order):
        lines = sections.get(key)
        if lines is None:
            # try Russian alias
            rus = next((r for r, e in aliases.items() if e == key), None)
            lines = sections.get(rus, []) if rus else []
        cell["source"] = [f"## {key}\n"] + [str(line) + "\n" for line in lines]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=2)


def segment_data(records: List[Dict[str, Any]], **filters: Any) -> List[Dict[str, Any]]:
    """Return subset of records matching simple equality filters."""
    return [r for r in records if all(r.get(k) == v for k, v in filters.items())]


def compute_custom_metric(records: List[Dict[str, Any]], expression: str) -> float:
    """Safely evaluate simple metric expressions on ``records``."""
    return safe_eval(expression, records)


# Replace export helpers with plugin implementations if available
_plug = plugin_loader.get_plugin("export")
if _plug:
    export_pdf = getattr(_plug, "export_pdf", export_pdf)  # type: ignore
    export_excel = getattr(_plug, "export_excel", export_excel)  # type: ignore
