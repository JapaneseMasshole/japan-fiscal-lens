"""Command-line entry point: `jfl <command>`."""

from __future__ import annotations

import argparse

from jfl.export import national_balance_sheet, national_flows
from jfl.fetch import mic, mof_financial_statements
from jfl.sources import load_sources

# Each fetcher takes (source, year or None for its default years, dry_run=...).
FETCHERS = {
    "mof-fs": mof_financial_statements.run_all,
    "mic-fiscal-indicators": mic.run_indicators,  # default: FY2015 onward
    "mic-unified-fs": mic.run_unified,  # default: latest year only (files are large)
    # Planned: "mof-settlement", "boj-flow-of-funds", "mic-kessan-card-pref", …
}


def cmd_sources(_: argparse.Namespace) -> None:
    for src in load_sources().values():
        status = "fetcher ready" if src.id in FETCHERS else "planned"
        years = ", ".join(str(y) for y in sorted(src.year_pages)) or "-"
        print(f"{src.id:26s} {src.level:8s} {status:14s} years: {years}")
        print(f"    {src.title_ja} / {src.title_en}")


def cmd_fetch(args: argparse.Namespace) -> None:
    sources = load_sources()
    ids = sorted(FETCHERS) if args.source == "all" else [args.source]
    year = None if args.year == "all" else int(args.year)
    for sid in ids:
        if sid not in sources:
            raise SystemExit(f"Unknown source {sid!r}. Run `jfl sources` to list them.")
        if sid not in FETCHERS:
            raise SystemExit(f"No fetcher implemented yet for {sid!r}.")
        print(f"== {sid}")
        FETCHERS[sid](sources[sid], year, dry_run=args.dry_run)


BUILDERS = {
    "national-balance-sheet": national_balance_sheet.build,
    "national-flows": national_flows.build,
}


def cmd_build(args: argparse.Namespace) -> None:
    names = sorted(BUILDERS) if args.dataset == "all" else [args.dataset]
    for name in names:
        if name not in BUILDERS:
            raise SystemExit(f"Unknown dataset {name!r}. Known: {', '.join(sorted(BUILDERS))}")
        csv_path, json_paths, skipped = BUILDERS[name]()
        for msg in skipped:
            print(f"skipped: {msg}")
        outputs = json_paths if isinstance(json_paths, list) else [json_paths]
        print(f"{name}: wrote {csv_path}, " + ", ".join(p.name for p in outputs))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="jfl", description="Japan Fiscal Lens data pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("sources", help="list datasets in data/sources.yaml")
    p.set_defaults(func=cmd_sources)

    p = sub.add_parser("fetch", help="download original files for a source")
    p.add_argument("source", help="source id (e.g. mof-fs) or 'all'")
    p.add_argument("--year", default="all", help="fiscal year (e.g. 2024), or 'all' = defaults")
    p.add_argument("--dry-run", action="store_true", help="show what would be downloaded")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("build", help="parse, validate and export a dataset for the site")
    p.add_argument("dataset", nargs="?", default="all", help="dataset id or 'all'")
    p.set_defaults(func=cmd_build)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
