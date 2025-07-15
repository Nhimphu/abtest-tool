import argparse
import json
from typing import List

from stats.ab_test import evaluate_abn_test


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
        print(json.dumps(res))
    else:
        for k, v in res.items():
            print(f"{k}: {v}")


def main(argv: List[str] | None = None) -> None:
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
