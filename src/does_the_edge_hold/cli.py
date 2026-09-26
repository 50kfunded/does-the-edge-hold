"""Command line entry point."""

import argparse

from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(prog="edge-hold")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    commands = parser.add_subparsers(dest="command")
    intraday_example = commands.add_parser("intraday-example", help="run the source-day study on made-up multi-window prices")
    intraday_example.add_argument("--output", type=Path, required=True)
    intraday_run = commands.add_parser("intraday-study", help="run only the separately locked source-day market subset")
    intraday_run.add_argument("--data-root", type=Path, required=True)
    intraday_run.add_argument("--cache-root", type=Path, required=True)
    intraday_run.add_argument("--plan", type=Path, default=Path("research/intraday/plan.json"))
    intraday_run.add_argument("--lock", type=Path, default=Path("research/intraday/plan.lock.json"))
    intraday_run.add_argument("--audit-root", type=Path, default=Path("reports/intraday/source-audit"))
    intraday_run.add_argument("--output", type=Path, required=True)
    intraday_audit = commands.add_parser("intraday-audit", help="check exact-precision sources and fixed weekday windows")
    intraday_audit.add_argument("--data-root", type=Path, required=True)
    intraday_audit.add_argument("--cache-root", type=Path, required=True)
    intraday_audit.add_argument("--plan", type=Path, default=Path("research/intraday/plan.json"))
    intraday_audit.add_argument("--output", type=Path, required=True)
    intraday_audit.add_argument("--source-code", nargs="*", type=Path, default=[])
    intraday_freeze = commands.add_parser("intraday-freeze", help="lock the separate within-date protocol before strategy returns")
    intraday_freeze.add_argument("--plan", type=Path, default=Path("research/intraday/plan.json"))
    intraday_freeze.add_argument("--audit", type=Path, required=True)
    intraday_freeze.add_argument("--output", type=Path, default=Path("research/intraday/plan.lock.json"))
    public_fetch = commands.add_parser("public-fetch", help="snapshot public daily spot candles without an account")
    public_fetch.add_argument("--output", type=Path, required=True)
    public_run = commands.add_parser("public-study", help="run the separately locked spot protocol")
    public_run.add_argument("--snapshot", type=Path, required=True)
    public_run.add_argument("--plan", type=Path, default=Path("research/public-spot/plan.json"))
    public_run.add_argument("--lock", type=Path, default=Path("research/public-spot/plan.lock.json"))
    public_run.add_argument("--output", type=Path, required=True)
    example = commands.add_parser("example", help="run the complete synthetic audit and report")
    example.add_argument("--output", type=Path, default=Path("runs/example"))
    audit = commands.add_parser("audit", help="inspect local Parquet bars without changing them")
    audit.add_argument("--data-root", type=Path, required=True)
    audit.add_argument("--output", type=Path, default=Path("runs/audit.json"))
    audit.add_argument("--skip-seconds", action="store_true")
    audit.add_argument("--semantic", action="store_true", help="also validate and hash canonical observations for version-2 locks")
    audit.add_argument("--public-summary", action="store_true",
                       help="omit per-bar investigation samples for publishing")
    origin = commands.add_parser("provenance", help="compare exports with the local source cache")
    origin.add_argument("--data-root", type=Path, required=True)
    origin.add_argument("--cache-root", type=Path, required=True)
    origin.add_argument("--output", type=Path, default=Path("runs/provenance.json"))
    gate = commands.add_parser("roll-check", help="decide whether empirical P&L may run")
    gate.add_argument("--audit", type=Path, required=True)
    gate.add_argument("--provenance", type=Path, required=True)
    gate.add_argument("--mapping-root", type=Path)
    gate.add_argument("--plan", type=Path, default=Path("research-plan.json"))
    gate.add_argument("--output", type=Path, default=Path("runs/roll-gate.json"))
    resolve = commands.add_parser("resolve-rolls", help="use Databento's free symbol resolver")
    resolve.add_argument("--audit", type=Path, required=True)
    resolve.add_argument("--provenance", type=Path, required=True)
    resolve.add_argument("--plan", type=Path, default=Path("research-plan.json"))
    resolve.add_argument("--markets", nargs="+")
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
    local = commands.add_parser("local-report", help="regenerate the local audit and study status")
    local.add_argument("--data-root", type=Path, required=True)
    local.add_argument("--cache-root", type=Path, required=True)
    local.add_argument("--mapping-root", type=Path)
    local.add_argument("--plan", type=Path, default=Path("research-plan.json"))
    local.add_argument("--lock", type=Path, default=Path("research-plan.lock.json"))
    local.add_argument("--output", type=Path, default=Path("runs/local"))
    args = parser.parse_args()
    if args.command == "intraday-example":
        from .intraday_example import run_example
        result = run_example(args.output)
        print(f"synthetic source-day cases: {result['runtime']['cases']}; {args.output / 'study/report.md'}")
    elif args.command == "intraday-study":
        from .intraday_study import run_study
        result = run_study(args.data_root, args.cache_root, args.plan, args.lock, args.audit_root, args.output)
        print(f"source-day cases: {result['runtime']['cases']}; {args.output / 'report.md'}")
    elif args.command == "intraday-audit":
        from .intraday_audit import run_audit
        result = run_audit(args.data_root, args.cache_root, args.plan, args.output, local_code_paths=args.source_code)
        print(f"source-day evidence: {result['readiness']['status']}; {args.output / 'audit.json'}")
    elif args.command == "intraday-freeze":
        from .intraday_plan import freeze
        result = freeze(args.plan, args.audit, args.output)
        print(f"frozen source-day protocol {result['plan_sha256']}")
    elif args.command == "public-fetch":
        import json
        from .public_data import fetch
        print(json.dumps(fetch(args.output), indent=2))
    elif args.command == "public-study":
        import json
        from .public_study import run_public
        print(json.dumps(run_public(args.snapshot, args.plan, args.lock, args.output), indent=2))
    elif args.command == "example":
        from .example import run_example

        report = run_example(args.output)
        print(f"ran {len({r['run_id'] for r in report['runs']})} synthetic cases on {report['minute_rows']:,} minute bars; report: {args.output / 'report.md'}")
    elif args.command == "audit":
        from .audit import audit_sources, public_summary, write_audit

        report = audit_sources(args.data_root, include_seconds=not args.skip_seconds, include_semantic=args.semantic)
        if args.public_summary:
            report = public_summary(report)
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
        from .plan import validate
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        validate(plan)
        decision = assess(audit_report, origin_report, args.mapping_root, plan=plan)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
        print(f"roll gate: {decision['status']} ({args.output})")
    elif args.command == "resolve-rolls":
        import json
        from .resolve import resolve_free

        audit_report = json.loads(args.audit.read_text(encoding="utf-8"))
        origin_report = json.loads(args.provenance.read_text(encoding="utf-8"))
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        path = resolve_free(audit_report, origin_report, args.output, plan=plan, markets=args.markets)
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
    elif args.command == "local-report":
        from .local_report import run_local_report

        status = run_local_report(args.data_root, args.cache_root, args.output,
                                  args.plan, args.lock, args.mapping_root)
        print(f"local study: {status['status']}; report: {args.output / 'report.md'}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
