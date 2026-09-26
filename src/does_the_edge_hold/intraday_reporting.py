"""Render source-day results from saved outcomes without rerunning selection."""
from pathlib import Path
from .intraday_plan import read

def render(output):
    output = Path(output)
    summary = read(output / "summary.json")
    lines = ["# the within-day study", "", f"i ran {summary['runtime']['cases']} cases. status: {summary['status']}.", "",
             f"the NQ development pick was `{summary['markets']['NQ']['primary_pick']}`. i kept it in later dates and the other markets.", "",
             summary["eligibility"], "", "real contract identities are unknown. the original roll-aware study stays blocked.", ""]
    for market in summary["markets"]:
        lines += [f"- [{market} outcomes]({market}/all-results.csv)"]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
