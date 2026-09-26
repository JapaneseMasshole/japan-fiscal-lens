"""Command-line entry point: `jfl <command>`."""

from __future__ import annotations

import argparse

from jfl.export import national_balance_sheet
from jfl.fetch import mof_financial_statements
from jfl.sources import load_sources

FETCHERS = {
    "mof-fs": mof_financial_statements.run,
    # Planned: "mof-settlement", "boj-flow-of-funds", "mic-unified-fs",
    #          "mic-kessan-card-pref", "mic-kessan-card-muni"
}


def cmd_sources(_: argparse.Namespace) -> None:
    for src in load_sources().values():
        status = "fetcher ready" if src.id in FETCHERS else "planned"
        years = ", ".join(str(y) for y in sorted(src.year_pages)) or "-"
        print(f"{src.id:26s} {src.level:8s} {status:14s} years: {years}")
        print(f"    {src.title_ja} / {src.title_en}")


def cmd_fetch(args: argparse.Namespace) -> None:
    sources = load_sources()
    if args.source not in sources:
        raise SystemExit(f"Unknown source {args.source!r}. Run `jfl sources` to list them.")
    fetcher = FETCHERS.get(args.source)
    if fetcher is None:
        raise SystemExit(f"No fetcher implemented yet for {args.source!r}.")
    years = sorted(sources[args.source].year_pages) if args.year == "all" else [int(args.year)]
    for year in years:
        fetcher(sources[args.source], year, dry_run=args.dry_run)


BUILDERS = {
    "national-balance-sheet": national_balance_sheet.build,
}


def cmd_build(args: argparse.Namespace) -> None:
    names = sorted(BUILDERS) if args.dataset == "all" else [args.dataset]
    for name in names:
        if name not in BUILDERS:
            raise SystemExit(f"Unknown dataset {name!r}. Known: {', '.join(sorted(BUILDERS))}")
        csv_path, json_path, skipped = BUILDERS[name]()
        for msg in skipped:
            print(f"skipped: {msg}")
        print(f"{name}: wrote {csv_path} and {json_path}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="jfl", description="Japan Fiscal Lens data pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("sources", help="list datasets in data/sources.yaml")
    p.set_defaults(func=cmd_sources)

    p = sub.add_parser("fetch", help="download original files for a source")
    p.add_argument("source", help="source id, e.g. mof-fs")
    p.add_argument("--year", default="all", help="fiscal year (e.g. 2024) or 'all'")
    p.add_argument("--dry-run", action="store_true", help="show what would be downloaded")
    p.set_defaults(func=cmd_fetch)

    p = sub.add_parser("build", help="parse, validate and export a dataset for the site")
    p.add_argument("dataset", nargs="?", default="all", help="dataset id or 'all'")
    p.set_defaults(func=cmd_build)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
