#!/usr/bin/env python3
"""Batch launch the NewsAPI scrape command for a range of dates."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_ENTRYPOINT = PROJECT_ROOT / "tw_cli.py"


def valid_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Formato de fecha inválido: {value}") from exc


def iter_dates(start: date, end: date) -> Iterable[date]:
    current = start
    delta = timedelta(days=1)
    while current <= end:
        yield current
        current += delta


def build_command(target_date: date) -> List[str]:
    return [
        sys.executable,
        str(CLI_ENTRYPOINT),
        "scrape",
        "--newsapi-only",
        "--date",
        target_date.isoformat(),
    ]


def run_batch(start: date, end: date, dry_run: bool) -> int:
    exit_code = 0
    for target_date in iter_dates(start, end):
        cmd = build_command(target_date)
        printable = " ".join(cmd)
        print(f"→ {printable}")
        if dry_run:
            continue
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"✖ Fecha {target_date.isoformat()} falló con código {result.returncode}")
            exit_code = result.returncode
        else:
            print(f"✔ Fecha {target_date.isoformat()} completada")
    return exit_code


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Automatiza scrapes de NewsAPI para un rango de fechas.")
    parser.add_argument("--start", type=valid_date, default=date(2025, 8, 27), help="Fecha inicial (YYYY-MM-DD)")
    parser.add_argument("--end", type=valid_date, default=date(2025, 9, 14), help="Fecha final inclusive (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Solo imprime los comandos sin ejecutarlos")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    if args.end < args.start:
        print("La fecha final debe ser mayor o igual a la inicial")
        return 1
    return run_batch(args.start, args.end, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
