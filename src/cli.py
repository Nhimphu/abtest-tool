import argparse
import json
import logging
import logging.config
from pathlib import Path
from typing import List

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore

from stats.ab_test import evaluate_abn_test

logger = logging.getLogger(__name__)


def _run_analysis(args: argparse.Namespace) -> None:
    """Run A/B test analysis from a JSON source file."""
    with open(args.source, "r", encoding="utf-8") as f:
        data = json.load(f)
    res = evaluate_abn_test(
        data["users_a"],
        data["conv_a"],
        data["users_b"],
        data["conv_b"],
        alpha=data.get("alpha", 0.05),
    )
    if args.output_format == "json":
        logger.info(json.dumps(res))
    else:
        for k, v in res.items():
            logger.info(f"{k}: {v}")


def main(argv: List[str] | None = None) -> None:
    cfg_path = Path(__file__).resolve().parents[1] / "logging.yaml"
    if cfg_path.exists() and yaml is not None:
        with cfg_path.open("r", encoding="utf-8") as f:
            logging.config.dictConfig(yaml.safe_load(f))
    else:  # pragma: no cover - fallback if yaml not available
        logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(prog="abtest-tool")
    subparsers = parser.add_subparsers(dest="command")

    pa = subparsers.add_parser("run-analysis", help="Run A/B test analysis")
    pa.add_argument("--source", required=True, help="Path to JSON data file")
    pa.add_argument("--flags", nargs="*", default=[], help="Optional flags")
    pa.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="json",
        help="Output format",
    )
    pa.set_defaults(func=_run_analysis)

    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
