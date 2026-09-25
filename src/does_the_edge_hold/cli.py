"""Command line entry point."""

import argparse

from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="edge-hold")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    commands = parser.add_subparsers(dest="command")
    example = commands.add_parser("example", help="make a small synthetic market")
    example.add_argument("--output", type=Path, default=Path("runs/example"))
    args = parser.parse_args()
    if args.command == "example":
        from .synthetic import make_bars

        args.output.mkdir(parents=True, exist_ok=True)
        path = args.output / "synthetic_bars.parquet"
        bars = make_bars()
        bars.to_parquet(path, index=False)
        print(f"made {len(bars):,} synthetic minute bars at {path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
