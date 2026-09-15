"""CLI — Multimodal Extract + Ontology Map."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from dg_compliance.extract.litellm_extractor import (
    DEFAULT_MODEL,
    EXAMPLE_MODELS,
    LiteLLMExtractor,
    resolve_model,
)
from dg_compliance.models.extraction import ExtractionResult
from dg_compliance.ontology.pipeline import run_ontology, write_ontology_outputs

app = typer.Typer(
    name="dg-compliance",
    help="DG Trade Compliance JP–SG prototype (Extract + Ontology Map)",
    no_args_is_help=True,
)
console = Console()


@app.command("extract")
def extract_cmd(
    input_path: Path = typer.Argument(..., exists=True, readable=True, help="SDS PDF / image / text"),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help=f"LiteLLM model id (default: DG_EXTRACT_MODEL or {DEFAULT_MODEL})",
    ),
    instruction: Optional[Path] = typer.Option(
        None,
        "--instruction",
        "-i",
        exists=True,
        readable=True,
        help="Optional shipping-instruction text file (chat/email)",
    ),
    instruction_text: Optional[str] = typer.Option(
        None,
        "--instruction-text",
        help="Optional shipping-instruction string",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Write ExtractionResult JSON here (default: stdout)",
    ),
    max_pages: int = typer.Option(8, "--max-pages", help="Max PDF pages to send to vision model"),
    show_raw: bool = typer.Option(False, "--show-raw", help="Include raw model text in console summary"),
) -> None:
    """Run Multimodal Extract (LiteLLM) on a SDS / shipping document."""
    instr = instruction_text
    if instruction is not None:
        instr = instruction.read_text(encoding="utf-8", errors="replace")

    resolved = resolve_model(model)
    console.print(f"[bold]Model:[/bold] {resolved}")
    console.print(f"[bold]Source:[/bold] {input_path}")

    extractor = LiteLLMExtractor(model=resolved, max_pages=max_pages)
    result = extractor.extract(input_path, instruction_text=instr)

    payload = result.to_pretty_dict()
    if not show_raw:
        payload.pop("raw_model_text", None)

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        console.print(f"[green]Wrote[/green] {output}")
    else:
        console.print_json(text)

    _print_extract_summary(result)
    if result.warnings:
        for w in result.warnings:
            console.print(f"[yellow]warning:[/yellow] {w}")


@app.command("map")
def map_cmd(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="ExtractionResult JSON (from extract)",
    ),
    co_load: Optional[list[Path]] = typer.Option(
        None,
        "--co-load",
        exists=True,
        readable=True,
        help="Additional ExtractionResult JSON(s) for same-container co-load",
    ),
    output_dir: Path = typer.Option(
        Path("dist/mapped"),
        "--output-dir",
        "-o",
        help="Directory for ontology_result.json and projection files",
    ),
    container_id: Optional[str] = typer.Option(None, "--container-id"),
    watt_hour: Optional[float] = typer.Option(
        None,
        "--watt-hour",
        help="Watt-hour for first item (UN3480 Case 4); applies to primary input only",
    ),
) -> None:
    """Run Ontology Map (deterministic) on extract JSON → JP/SG drafts."""
    paths = [input_path] + list(co_load or [])
    extractions = [
        ExtractionResult.model_validate_json(p.read_text(encoding="utf-8")) for p in paths
    ]
    watt_hours: list[float | None] | None = None
    if watt_hour is not None:
        watt_hours = [watt_hour] + [None] * (len(extractions) - 1)

    result = run_ontology(
        extractions, container_id=container_id, watt_hours=watt_hours
    )
    written = write_ontology_outputs(result, output_dir)

    _print_ontology_summary(result)
    for path in written:
        console.print(f"[green]Wrote[/green] {path}")

    if result.export_blocked:
        console.print("[red]Export blocked[/red] (segregation / fatal findings)")
        raise typer.Exit(code=2)


@app.command("run")
def run_cmd(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="ExtractionResult JSON (same as map)",
    ),
    co_load: Optional[list[Path]] = typer.Option(
        None,
        "--co-load",
        exists=True,
        readable=True,
        help="Additional ExtractionResult JSON(s) for co-load",
    ),
    output_dir: Path = typer.Option(
        Path("dist/run"),
        "--output-dir",
        "-o",
    ),
    container_id: Optional[str] = typer.Option(None, "--container-id"),
    watt_hour: Optional[float] = typer.Option(None, "--watt-hour"),
) -> None:
    """Alias for `map` — Ontology Map only (extract separately)."""
    map_cmd(
        input_path=input_path,
        co_load=co_load,
        output_dir=output_dir,
        container_id=container_id,
        watt_hour=watt_hour,
    )


@app.command("models")
def models_cmd() -> None:
    """Show supported LiteLLM providers and example model ids."""
    examples = "\n".join(f"  {m}" for m in EXAMPLE_MODELS)
    console.print(
        f"""
[bold]DG Multimodal Extract — LiteLLM providers[/bold]

Supported: [cyan]Gemini[/cyan] · [cyan]OpenAI[/cyan] · [cyan]Anthropic[/cyan]

Default model:
  {DEFAULT_MODEL}

Examples:
{examples}

Env (see .env.example):
  DG_EXTRACT_MODEL={DEFAULT_MODEL}
  GEMINI_API_KEY=...      # for gemini/*
  OPENAI_API_KEY=...      # for openai/*
  ANTHROPIC_API_KEY=...   # for anthropic/*

CLI:
  uv run dg-compliance extract ./data/samples/sds_un1170_ethanol.txt
  uv run dg-compliance map dist/out.json -o dist/mapped/
  uv run dg-compliance map a.json --co-load b.json -o dist/mapped/
""".strip()
    )


def _print_extract_summary(result) -> None:
    f = result.fields
    table = Table(title="Extracted DG fields", show_header=True, header_style="bold")
    table.add_column("Field")
    table.add_column("Value")
    rows = [
        ("UN number", f.un_number),
        ("PSN", f.proper_shipping_name),
        ("Class", f.hazard_class),
        ("Subsidiary risk", f.subsidiary_risk),
        ("Packing group", None if f.packing_group is None else f.packing_group.value),
        ("Flash point °C", f.flash_point_c),
        ("Marine pollutant", f.marine_pollutant),
        ("Packaging", f.packaging_type),
        ("Is DG", f.is_dangerous_goods),
        ("Language", f.language_detected),
    ]
    for k, v in rows:
        table.add_row(k, "—" if v is None else str(v))
    console.print(table)

    if result.evidence:
        ev = Table(title="Evidence", show_header=True, header_style="bold")
        ev.add_column("Field")
        ev.add_column("Page")
        ev.add_column("Snippet")
        for e in result.evidence:
            ev.add_row(
                e.field,
                "—" if e.page_no is None else str(e.page_no),
                (e.snippet[:120] + "…") if len(e.snippet) > 120 else e.snippet,
            )
        console.print(ev)


def _print_ontology_summary(result) -> None:
    table = Table(title="Ontology Map", show_header=True, header_style="bold")
    table.add_column("Item")
    table.add_column("Value")
    table.add_row("export_blocked", str(result.export_blocked))
    table.add_row("skip_dg_forms", str(result.skip_dg_forms))
    table.add_row("tags", ", ".join(result.tags) or "—")
    console.print(table)

    items = Table(title="Canonical items", show_header=True, header_style="bold")
    items.add_column("UN")
    items.add_column("Class")
    items.add_column("PSA")
    items.add_column("DG")
    for it in result.shipment.items:
        items.add_row(
            it.un_number or "—",
            it.hazard_class or "—",
            it.psa_group.value if it.psa_group else "—",
            str(it.is_dangerous_goods),
        )
    console.print(items)

    if result.findings:
        ftab = Table(title="Findings", show_header=True, header_style="bold")
        ftab.add_column("Severity")
        ftab.add_column("Code")
        ftab.add_column("Message")
        for f in result.findings:
            ftab.add_row(f.severity.value, f.code, f.message)
        console.print(ftab)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
