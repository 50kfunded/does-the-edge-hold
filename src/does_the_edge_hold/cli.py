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
    origin = commands.add_parser("provenance", help="compare exports with the local source cache")
    origin.add_argument("--data-root", type=Path, required=True)
    origin.add_argument("--cache-root", type=Path, required=True)
    origin.add_argument("--output", type=Path, default=Path("runs/provenance.json"))
    gate = commands.add_parser("roll-check", help="decide whether empirical P&L may run")
    gate.add_argument("--audit", type=Path, required=True)
    gate.add_argument("--provenance", type=Path, required=True)
    gate.add_argument("--mapping-root", type=Path)
    gate.add_argument("--output", type=Path, default=Path("runs/roll-gate.json"))
    resolve = commands.add_parser("resolve-rolls", help="use Databento's free symbol resolver")
    resolve.add_argument("--audit", type=Path, required=True)
    resolve.add_argument("--provenance", type=Path, required=True)
    resolve.add_argument("--output", type=Path, default=Path("runs/roll-mapping"))
    freeze = commands.add_parser("freeze", help="lock the research plan before grid runs")
    freeze.add_argument("--plan", type=Path, default=Path("research-plan.json"))
    freeze.add_argument("--audit", type=Path, required=True)
    freeze.add_argument("--output", type=Path, default=Path("research-plan.lock.json"))
    research = commands.add_parser("research", help="run the locked local study if rolls are verified")
    research.add_argument("--data-root", type=Path, required=True)
    research.add_argument("--mapping-root", type=Path, required=True)
    research.add_argument("--audit", type=Path, default=Path("reports/local-data-audit.json"))
    research.add_argument("--provenance", type=Path, default=Path("reports/local-provenance.json"))
    research.add_argument("--plan", type=Path, default=Path("research-plan.json"))
    research.add_argument("--lock", type=Path, default=Path("research-plan.lock.json"))
    research.add_argument("--output", type=Path, default=Path("runs/empirical"))
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
    elif args.command == "provenance":
        import json
        from .provenance import verify_minute_origin

        report = {"markets": [verify_minute_origin(args.data_root, args.cache_root, market)
                              for market in ("NQ", "ES", "YM", "GC", "CL")],
                  "roll_gate": "source rule identified; date-to-contract mapping still required"}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"checked five cached series at {args.output}")
    elif args.command == "roll-check":
        import json
        from .roll_gate import assess

        audit_report = json.loads(args.audit.read_text(encoding="utf-8"))
        origin_report = json.loads(args.provenance.read_text(encoding="utf-8"))
        decision = assess(audit_report, origin_report, args.mapping_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
        print(f"roll gate: {decision['status']} ({args.output})")
    elif args.command == "resolve-rolls":
        import json
        from .resolve import resolve_free

        audit_report = json.loads(args.audit.read_text(encoding="utf-8"))
        origin_report = json.loads(args.provenance.read_text(encoding="utf-8"))
        path = resolve_free(audit_report, origin_report, args.output)
        print(f"saved local roll evidence at {path}")
    elif args.command == "freeze":
        from .plan import freeze as freeze_plan

        lock = freeze_plan(args.plan, args.audit, args.output)
        print(f"frozen plan {lock['plan_sha256'][:12]} at {args.output}")
    elif args.command == "research":
        from .experiments import run_empirical

        report = run_empirical(args.data_root, args.mapping_root, args.audit,
                               args.provenance, args.plan, args.lock, args.output)
        print(f"completed historical evaluation for {len(report['markets'])} markets at {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
