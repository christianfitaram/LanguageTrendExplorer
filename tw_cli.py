from __future__ import annotations

import asyncio
import inspect
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import typer
from rich import box
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.traceback import install as rich_traceback_install

try:
    import uvloop  # type: ignore
except Exception:
    uvloop = None

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

app = typer.Typer(add_completion=True, no_args_is_help=True, help="Trending Words CLI")
console = Console()

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
try:
    import importlib

    sys.modules.setdefault("custom_scrapers", importlib.import_module("pipeline_sample.custom_scrapers"))
    sys.modules.setdefault("news_api_scraper", importlib.import_module("pipeline_sample.news_api_scraper"))
except Exception:
    pass
# Pretty tracebacks
rich_traceback_install(show_locals=False, width=120, extra_lines=2, word_wrap=True)


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False, markup=True)],
    )


@dataclass
class Target:
    candidates: List[str]

    def resolve(self) -> Callable[..., Any]:
        errs: List[str] = []
        for path in self.candidates:
            mod_name, _, func_name = path.partition(":")
            try:
                mod = importlib.import_module(mod_name)
            except Exception as e:
                errs.append(f"import {mod_name!r} failed: {e}")
                continue
            func = getattr(mod, func_name or "main", None)
            if callable(func):
                return func
            errs.append(f"{path}: callable not found")
        raise RuntimeError("No suitable target found. Tried:\n- " + "\n- ".join(errs))

    def call(self, **cli_kwargs: Any) -> Any:
        func = self.resolve()
        sig = inspect.signature(func)
        bound_kwargs = {k: v for k, v in cli_kwargs.items() if k in sig.parameters}
        if inspect.iscoroutinefunction(func):
            return asyncio.get_event_loop().run_until_complete(func(**bound_kwargs))
        return func(**bound_kwargs)


TARGETS: Dict[str, Target] = {
    "run": Target(["pipeline_sample.exec_gather:main"]),
    "scrape": Target(["pipeline_sample.exec_gather:main"]),
    "classify": Target(["pipeline_sample.exec_gather:main"]),
    "clean": Target(["pipeline_sample.exec_cleaner:clean_articles"]),
    "trends": Target(["pipeline_trend_analyzer.exec_trends:main"]),
}


def load_env(dotenv_path: Optional[str]) -> None:
    if load_dotenv:
        if dotenv_path and os.path.exists(dotenv_path):
            load_dotenv(dotenv_path, override=False)
        else:
            load_dotenv(override=False)


def set_event_loop_policy() -> None:
    if uvloop and sys.platform != "win32":
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@app.callback()
def main(
        ctx: typer.Context,
        dotenv_path: Optional[str] = typer.Option(None, help="Path to .env file"),
        verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose logging"),
):
    set_event_loop_policy()
    load_env(dotenv_path)
    setup_logging(verbose)


def banner(title: str) -> None:
    console.print(Panel.fit(f"[b]{title}[/b]", box=box.HEAVY, border_style="cyan"))


@app.command()
def run(
        newsapi_only: bool = typer.Option(False, help="Use only NewsAPI-based scrapers"),
        date: Optional[str] = typer.Option(None, help="YYYY-MM-DD (applies to NewsAPI scrapers)"),
):
    banner("Run: end-to-end pipeline")
    TARGETS["run"].call(newsapi_only=newsapi_only, target_date=date)


@app.command()
def scrape(
        newsapi_only: bool = typer.Option(False, help="Use only NewsAPI-based scrapers"),
        date: Optional[str] = typer.Option(None, help="YYYY-MM-DD (applies to NewsAPI scrapers)"),
):
    banner("Scrape: intake sources")
    TARGETS["scrape"].call(newsapi_only=newsapi_only, target_date=date)


@app.command()
def classify(
        newsapi_only: bool = typer.Option(False, help="Use only NewsAPI-based scrapers"),
        date: Optional[str] = typer.Option(None, help="YYYY-MM-DD (applies to NewsAPI scrapers)"),
):
    banner("Classify: topics/sentiment/summaries")
    TARGETS["classify"].call(newsapi_only=newsapi_only, target_date=date)


@app.command()
def clean(sample_id: Optional[str] = typer.Option(None, help="Sample ID like '2-2025-08-10'")):
    banner("Clean: text normalization & noun extraction")
    TARGETS["clean"].call(sample_id=sample_id)


@app.command()
def trends(
        sample: Optional[str] = typer.Option(None, help="Sample ID, e.g. '2-2025-08-18' (defaults to last sample)"),
        limit: int = typer.Option(15, help="Max clusters to build/rank (logical cap inside code)"),
        persist: bool = typer.Option(True, "--persist/--dry-run", help="Persist to trend_threads/daily_trends"),
        date: Optional[str] = typer.Option(None, help="Override date (YYYY-MM-DD); defaults to today (UTC)"),
        print_top: int = typer.Option(5, help="How many threads to print"),
):
    banner("Trends: build → rank → link")
    TARGETS["trends"].call(sample_id=sample, limit=limit, persist=persist, date=date, print_top=print_top)


if __name__ == "__main__":
    app()
