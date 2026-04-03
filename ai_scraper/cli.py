"""
CLI interface for AI Scraper.

Usage examples:
    # Scrape apartments from a page
    ai-scraper scrape https://example.com/listings --schema apartments --output results.json

    # Scrape with a custom schema
    ai-scraper scrape https://example.com --fields "name,price,url" --output results.csv

    # Ask a question about a page
    ai-scraper ask https://example.com "What products are for sale?"

    # List available schemas
    ai-scraper schemas
"""

import json
import logging
import os
import sys

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler
from rich import print as rprint

from ai_scraper import __version__

console = Console()

BANNER = r"""
[bold cyan]
   █████╗ ██╗    ███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗
  ██╔══██╗██║    ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
  ███████║██║    ███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝
  ██╔══██║██║    ╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗
  ██║  ██║██║    ███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║
  ╚═╝  ╚═╝╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝
[/bold cyan]
[dim]  Universal AI-Powered Web Data Extraction Engine · v{version}[/dim]
"""


def _setup_logging(verbose: bool):
    """Configure rich logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_time=False)],
    )


def _get_scraper(provider, api_key, model, headless):
    """Create an AIScraper instance from CLI args."""
    from ai_scraper.core import AIScraper

    # Try env vars if not provided
    if not api_key:
        env_map = {
            "openrouter": "OPENROUTER_API_KEY",
            "openai": "OPENAI_API_KEY",
            "kilo": "KILO_API_KEY",
        }
        env_var = env_map.get(provider, "AI_SCRAPER_API_KEY")
        api_key = os.environ.get(env_var, "")
        if not api_key:
            api_key = os.environ.get("AI_SCRAPER_API_KEY", "")

    if not api_key and provider != "ollama":
        console.print(
            "[bold red]Error:[/bold red] No API key provided. "
            f"Use --api-key or set {env_map.get(provider, 'AI_SCRAPER_API_KEY')} env var."
        )
        sys.exit(1)

    return AIScraper(
        provider=provider,
        api_key=api_key,
        model=model,
        headless=headless,
    )


@click.group()
@click.version_option(__version__)
def main():
    """AI Scraper — point at any website, extract structured data."""
    pass


@main.command()
@click.argument("url")
@click.option("--schema", "-s", default="apartments", help="Schema name or 'custom'")
@click.option("--fields", "-f", default=None, help="Comma-separated custom field names")
@click.option("--instructions", "-i", default="", help="Extra instructions for the LLM")
@click.option("--output", "-o", default=None, help="Output file (json or csv)")
@click.option("--provider", "-p", default="openrouter", help="LLM provider")
@click.option("--api-key", "-k", default="", help="API key (or use env var)")
@click.option("--model", "-m", default=None, help="Specific model to use")
@click.option("--no-headless", is_flag=True, help="Show browser window")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def scrape(url, schema, fields, instructions, output, provider, api_key, model, no_headless, verbose):
    """Scrape a URL and extract structured data."""
    _setup_logging(verbose)
    rprint(BANNER.format(version=__version__))

    # Build schema
    if fields:
        extraction_schema = {f.strip(): f"The {f.strip()} value" for f in fields.split(",")}
        console.print(f"[cyan]Custom schema:[/cyan] {list(extraction_schema.keys())}")
    else:
        from ai_scraper.schemas import Schema
        extraction_schema = Schema.get(schema)
        console.print(f"[cyan]Using schema:[/cyan] {schema.upper()}")

    console.print(f"[cyan]Target URL:[/cyan] {url}")
    console.print(f"[cyan]Provider:[/cyan] {provider} / {model or 'default'}")
    console.print()

    with _get_scraper(provider, api_key, model, not no_headless) as scraper:
        with console.status("[bold green]Scraping...[/bold green]"):
            results = scraper.scrape(url, extraction_schema, instructions)

        if not results:
            console.print("[yellow]⚠  No results found.[/yellow]")
            return

        # Display results
        _display_results(results, extraction_schema)

        # Save if output specified
        if output:
            if output.endswith(".csv"):
                scraper.save_csv(results, output)
            else:
                scraper.save_json(results, output)
            console.print(f"\n[green]✓  Saved {len(results)} results to {output}[/green]")


@main.command()
@click.argument("url")
@click.argument("question")
@click.option("--provider", "-p", default="openrouter", help="LLM provider")
@click.option("--api-key", "-k", default="", help="API key")
@click.option("--model", "-m", default=None, help="Specific model")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def ask(url, question, provider, api_key, model, verbose):
    """Ask a question about a web page's content."""
    _setup_logging(verbose)
    rprint(BANNER.format(version=__version__))

    console.print(f"[cyan]URL:[/cyan] {url}")
    console.print(f"[cyan]Question:[/cyan] {question}")
    console.print()

    with _get_scraper(provider, api_key, model, True) as scraper:
        with console.status("[bold green]Thinking...[/bold green]"):
            answer = scraper.ask_page(url, question)

        console.print(Panel(answer, title="[bold green]Answer[/bold green]", border_style="green"))


@main.command()
def schemas():
    """List all available extraction schemas."""
    rprint(BANNER.format(version=__version__))

    from ai_scraper.schemas import Schema

    all_schemas = Schema.list_all()

    for name, fields in all_schemas.items():
        table = Table(title=f"📋 {name}", show_header=True, header_style="bold cyan")
        table.add_column("Field", style="green", min_width=20)
        table.add_column("Description", style="dim")

        for field, desc in fields.items():
            table.add_row(field, desc)

        console.print(table)
        console.print()

    console.print(f"[dim]{len(all_schemas)} schemas available. Use --schema NAME with the scrape command.[/dim]")


@main.command()
@click.argument("urls", nargs=-1, required=True)
@click.option("--schema", "-s", default="apartments", help="Schema name")
@click.option("--output", "-o", default="results.json", help="Output file")
@click.option("--provider", "-p", default="openrouter", help="LLM provider")
@click.option("--api-key", "-k", default="", help="API key")
@click.option("--model", "-m", default=None, help="Specific model")
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def batch(urls, schema, output, provider, api_key, model, verbose):
    """Scrape multiple URLs and combine results."""
    _setup_logging(verbose)
    rprint(BANNER.format(version=__version__))

    from ai_scraper.schemas import Schema
    extraction_schema = Schema.get(schema)

    console.print(f"[cyan]Batch scraping {len(urls)} URLs with schema:[/cyan] {schema.upper()}")
    console.print()

    with _get_scraper(provider, api_key, model, True) as scraper:
        results = scraper.scrape_multiple(list(urls), extraction_schema)

        if not results:
            console.print("[yellow]⚠  No results found across any URL.[/yellow]")
            return

        _display_results(results, extraction_schema)

        if output.endswith(".csv"):
            scraper.save_csv(results, output)
        else:
            scraper.save_json(results, output)

        console.print(f"\n[green]✓  Saved {len(results)} total results to {output}[/green]")


def _display_results(results: list, schema: dict):
    """Pretty-print results as a rich table."""
    table = Table(
        title=f"[bold]🔍 {len(results)} Results Found[/bold]",
        show_header=True,
        header_style="bold magenta",
        show_lines=True,
    )

    # Use schema keys as columns, limit to first 6 for readability
    columns = list(schema.keys())[:6]
    for col in columns:
        table.add_column(col.replace("_", " ").title(), max_width=40)

    for item in results[:25]:  # Show max 25 rows
        row = []
        for col in columns:
            val = str(item.get(col, "—"))
            if len(val) > 40:
                val = val[:37] + "..."
            row.append(val)
        table.add_row(*row)

    if len(results) > 25:
        console.print(f"[dim](Showing first 25 of {len(results)} results)[/dim]")

    console.print(table)


if __name__ == "__main__":
    main()
