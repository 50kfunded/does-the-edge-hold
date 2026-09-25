"""Command line entry point."""

import argparse

from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="edge-hold")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    commands = parser.add_subparsers(dest="command")
    example = commands.add_parser("example", help="make a small synthetic market")
    example.add_argument("--output", type=Path, default=Path("runs/example"))
    audit = commands.add_parser("audit", help="inspect local Parquet bars without changing them")
    audit.add_argument("--data-root", type=Path, required=True)
    audit.add_argument("--output", type=Path, default=Path("runs/audit.json"))
    audit.add_argument("--skip-seconds", action="store_true")
    args = parser.parse_args()
    if args.command == "example":
        from .synthetic import make_bars

        args.output.mkdir(parents=True, exist_ok=True)
        path = args.output / "synthetic_bars.parquet"
        bars = make_bars()
        bars.to_parquet(path, index=False)
        print(f"made {len(bars):,} synthetic minute bars at {path}")
    elif args.command == "audit":
        from .audit import audit_sources, write_audit

        report = audit_sources(args.data_root, include_seconds=not args.skip_seconds)
        write_audit(report, args.output)
        print(f"audited {len(report['files'])} source files at {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
