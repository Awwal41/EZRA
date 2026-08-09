"""EZRA command-line interface (HPC / laptop)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ezra import __version__
from ezra.config import load_config, resolve_models_dir
from ezra.downloader import ModelDownloader, disk_usage
from ezra.gallery import ModelGallery

console = Console(stderr=False)


def _fmt_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(n)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def _downloader(ctx: click.Context) -> ModelDownloader:
    config = ctx.obj["config"]
    gallery = ctx.obj["gallery"]
    return ModelDownloader(
        config,
        gallery,
        on_log=lambda msg: console.print(msg),
    )


@click.group()
@click.version_option(__version__, prog_name="ezra")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path, exists=False),
    default=None,
    help="Path to ezra.yaml (else EZRA_CONFIG / cwd / ~/.ezra / packaged default).",
)
@click.option(
    "--models-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Where to store model weights (also: EZRA_MODELS_DIR or local.models_dir in ezra.yaml).",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path | None, models_dir: Path | None) -> None:
    """EZRA - Easy Zero-setup Routing Assistant for local & HPC LLMs."""
    ctx.ensure_object(dict)
    config = load_config(config_path)
    if models_dir is not None:
        config.models_dir = resolve_models_dir(cli_override=models_dir)
    # Let vendor helpers see yaml CLI paths when env is unset.
    if config.peekaboo_cli and not os.environ.get("EZRA_PEEKABOO_CLI"):
        os.environ["EZRA_PEEKABOO_CLI"] = config.peekaboo_cli
    if config.gog_cli and not os.environ.get("EZRA_GOG_CLI"):
        os.environ["EZRA_GOG_CLI"] = config.gog_cli
    if config.gog_account and not os.environ.get("GOG_ACCOUNT"):
        os.environ["GOG_ACCOUNT"] = config.gog_account
    if config.openclaw_cli and not os.environ.get("EZRA_OPENCLAW_CLI"):
        os.environ["EZRA_OPENCLAW_CLI"] = config.openclaw_cli
    ctx.obj["config"] = config
    ctx.obj["gallery"] = ModelGallery()


@main.group("models")
def models_group() -> None:
    """Browse and download curated free/open models."""


@models_group.command("list")
@click.option("-q", "--query", default=None, help="Filter by name/description substring.")
@click.option("--tag", default=None, help="Filter by tag (e.g. chemistry, hpc, reasoning).")
@click.option("--science", is_flag=True, help="Only models with science_tags.")
@click.option("--format", "fmt", default=None, help="Filter by format: gguf | safetensors.")
@click.option("--max-size", type=float, default=None, help="Max size in billions of params.")
@click.option("--include-gated/--no-gated", default=True, help="Show gated HF models.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
@click.pass_context
def models_list(
    ctx: click.Context,
    query: str | None,
    tag: str | None,
    science: bool,
    fmt: str | None,
    max_size: float | None,
    include_gated: bool,
    as_json: bool,
) -> None:
    """List available free models in the EZRA gallery."""
    gallery: ModelGallery = ctx.obj["gallery"]
    dl = _downloader(ctx)
    specs = gallery.list(
        query=query,
        tag=tag,
        science_only=science,
        include_gated=include_gated,
        max_size_b=max_size,
        format=fmt,
    )
    if as_json:
        payload = [
            {
                "name": s.name,
                "repo_id": s.repo_id,
                "format": s.format,
                "quant": s.quant,
                "params": s.params,
                "size_b": s.size_b,
                "license": s.license,
                "gated": s.gated,
                "science_tags": list(s.science_tags),
                "tags": list(s.tags),
                "description": s.description,
                "installed": dl.is_installed(s),
                "path": str(dl.model_dir(s)) if dl.is_installed(s) else None,
            }
            for s in specs
        ]
        click.echo(json.dumps(payload, indent=2))
        return

    table = Table(title=f"EZRA free model gallery ({len(specs)})")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Size", no_wrap=True)
    table.add_column("Fmt", no_wrap=True)
    table.add_column("Tags")
    table.add_column("In", no_wrap=True)
    table.add_column("Description")
    for s in specs:
        installed = "Y" if dl.is_installed(s) else ""
        gated = "*" if s.gated else ""
        tags = ",".join(list(s.science_tags)[:2] or list(s.tags)[:2]) or "-"
        table.add_row(
            f"{s.name}{gated}",
            s.params or f"{s.size_b}B",
            s.format[:4],
            tags,
            installed,
            s.description,
        )
    console.print(table)
    console.print(
        f"\nModels dir: [bold]{ctx.obj['config'].models_dir}[/bold]\n"
        "  (* = gated HF license)\n"
        "Choose storage: [green]ezra --models-dir /path …[/green] "
        "or [green]export EZRA_MODELS_DIR=/path[/green]\n"
        "Download one:  [green]ezra models download <name>[/green]\n"
        "Download all:  [green]ezra models download --all[/green]"
    )


@models_group.command("download")
@click.argument("names", nargs=-1)
@click.option(
    "--all",
    "all_models",
    is_flag=True,
    help="Download every matching free gallery model.",
)
@click.option("--tag", default=None, help="With --all, only models that have this tag.")
@click.option("--science", is_flag=True, help="With --all, only science-tagged models.")
@click.option("--format", "fmt", default=None, help="With --all, filter format.")
@click.option("--max-size", type=float, default=None, help="With --all, max size (B params).")
@click.option(
    "--include-gated/--no-gated",
    default=False,
    help="Include gated models (requires HF_TOKEN + accepted license).",
)
@click.option("--quant", default=None, help="Override quantization preference (e.g. Q4_K_M).")
@click.option("--force", is_flag=True, help="Re-download even if already present.")
@click.option("--dry-run", is_flag=True, help="Show what would be downloaded.")
@click.option(
    "--workers",
    type=int,
    default=None,
    help="Parallel downloads (default from config, usually 2).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON results.")
@click.pass_context
def models_download(
    ctx: click.Context,
    names: tuple[str, ...],
    all_models: bool,
    tag: str | None,
    science: bool,
    fmt: str | None,
    max_size: float | None,
    include_gated: bool,
    quant: str | None,
    force: bool,
    dry_run: bool,
    workers: int | None,
    as_json: bool,
) -> None:
    """Download a named model, several names, or --all free models.

    \b
    Examples (HPC-friendly):
      ezra models download qwen2.5-7b-instruct
      ezra models download chemllm-7b matscibert
      ezra models download --all --no-gated
      ezra models download --all --tag chemistry
      ezra models download --all --max-size 8 --format gguf
    """
    if not names and not all_models:
        raise click.UsageError(
            "Provide model NAME(s) or use --all. Try: ezra models list"
        )

    dl = _downloader(ctx)
    results = dl.download_many(
        list(names) if names else None,
        all_models=all_models or not names,
        tag=tag,
        science_only=science,
        include_gated=include_gated,
        max_size_b=max_size,
        format=fmt,
        quant=quant,
        force=force,
        dry_run=dry_run,
        workers=workers,
    )

    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        table = Table(title="Download results")
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Seconds", justify="right")
        table.add_column("Message")
        for r in results:
            style = {
                "downloaded": "green",
                "already_present": "yellow",
                "skipped": "dim",
                "failed": "red",
            }.get(r.status, "")
            table.add_row(r.name, f"[{style}]{r.status}[/{style}]", f"{r.seconds:.1f}", r.message)
        console.print(table)

    failed = [r for r in results if r.status == "failed"]
    if failed:
        sys.exit(1)


@models_group.command("info")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def models_info(ctx: click.Context, name: str, as_json: bool) -> None:
    """Show details for one gallery model."""
    gallery: ModelGallery = ctx.obj["gallery"]
    dl = _downloader(ctx)
    try:
        spec = gallery.get(name)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    installed = dl.is_installed(spec)
    path = dl.model_dir(spec)
    payload = {
        "name": spec.name,
        "repo_id": spec.repo_id,
        "format": spec.format,
        "quant": spec.quant,
        "params": spec.params,
        "size_b": spec.size_b,
        "license": spec.license,
        "gated": spec.gated,
        "science_tags": list(spec.science_tags),
        "tags": list(spec.tags),
        "description": spec.description,
        "file_pattern": spec.file_pattern,
        "recommended_ram_gb": spec.recommended_ram_gb,
        "installed": installed,
        "path": str(path) if installed else None,
        "bytes_on_disk": disk_usage(path) if installed else 0,
    }
    if as_json:
        click.echo(json.dumps(payload, indent=2))
        return
    console.print(payload)


@models_group.command("status")
@click.option("--json", "as_json", is_flag=True)
@click.pass_context
def models_status(ctx: click.Context, as_json: bool) -> None:
    """Show installed models and disk usage."""
    config = ctx.obj["config"]
    dl = _downloader(ctx)
    installed = dl.list_installed()
    total = disk_usage(config.models_dir)
    rows = []
    for s in installed:
        path = dl.model_dir(s)
        rows.append(
            {
                "name": s.name,
                "path": str(path),
                "bytes": disk_usage(path),
                "format": s.format,
            }
        )
    if as_json:
        click.echo(
            json.dumps(
                {
                    "models_dir": str(config.models_dir),
                    "count": len(rows),
                    "total_bytes": total,
                    "models": rows,
                },
                indent=2,
            )
        )
        return

    console.print(f"Models dir: [bold]{config.models_dir}[/bold]")
    console.print(f"Installed:  [bold]{len(rows)}[/bold]  Total: {_fmt_bytes(total)}")
    if not rows:
        console.print("Nothing installed yet. Try: [green]ezra models download --all --max-size 8[/green]")
        return
    table = Table(title="Installed models")
    table.add_column("Name", style="cyan")
    table.add_column("Format")
    table.add_column("Size")
    table.add_column("Path")
    for row in rows:
        table.add_row(row["name"], row["format"], _fmt_bytes(row["bytes"]), row["path"])
    console.print(table)


@models_group.command("remove")
@click.argument("names", nargs=-1, required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def models_remove(ctx: click.Context, names: tuple[str, ...], dry_run: bool) -> None:
    """Delete installed model directories."""
    dl = _downloader(ctx)
    for name in names:
        result = dl.remove(name, dry_run=dry_run)
        style = "green" if result.status != "failed" else "red"
        console.print(f"[{style}]{result.status}[/{style}] {result.name}: {result.message}")


@models_group.command("recommend")
@click.argument("keyword", required=False, default=None)
@click.option("--limit", type=int, default=5, show_default=True, help="Max recommendations.")
@click.option("--tag", default=None, help="Require this gallery tag.")
@click.option("--science", is_flag=True, help="Only models with science_tags.")
@click.option("--format", "fmt", default=None, help="Filter by format: gguf | safetensors.")
@click.option(
    "--include-gated/--no-gated",
    default=False,
    help="Include gated HF models (default: exclude).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
@click.pass_context
def models_recommend(
    ctx: click.Context,
    keyword: str | None,
    limit: int,
    tag: str | None,
    science: bool,
    fmt: str | None,
    include_gated: bool,
    as_json: bool,
) -> None:
    """Recommend open models that fit this machine (optional keyword).

    \b
    Examples:
      ezra models recommend
      ezra models recommend chemistry
      ezra models recommend reasoning --limit 5
      ezra models recommend --format gguf --science
    """
    from ezra.hardware import probe_system
    from ezra.recommend import recommend

    gallery: ModelGallery = ctx.obj["gallery"]
    system = probe_system()
    picks = recommend(
        gallery,
        system,
        keyword=keyword,
        tag=tag,
        science_only=science,
        include_gated=include_gated,
        format=fmt,
        limit=limit,
    )

    if as_json:
        click.echo(
            json.dumps(
                {
                    "system": {
                        "ram_total_gb": system.ram_total_gb,
                        "cpu_count": system.cpu_count,
                        "effective_memory_gb": system.effective_memory_gb,
                        "has_gpu": system.has_gpu,
                        "gpus": [
                            {"name": g.name, "vram_gb": round(g.vram_gb, 2)}
                            for g in system.gpus
                        ],
                    },
                    "keyword": keyword,
                    "recommendations": [r.to_dict() for r in picks],
                },
                indent=2,
            )
        )
        return

    console.print("[bold]System[/bold]")
    for line in system.summary_lines():
        console.print(f"  {line}")
    if keyword:
        console.print(f"  Keyword:   {keyword}")
    console.print()

    if not picks:
        console.print(
            "[yellow]No gallery models fit this machine with the given filters.[/yellow]\n"
            "Try a broader keyword, --include-gated, or free up RAM / use a GPU node."
        )
        return

    table = Table(title=f"Recommended models ({len(picks)})")
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Size", no_wrap=True)
    table.add_column("Fmt", no_wrap=True)
    table.add_column("Need", no_wrap=True)
    table.add_column("Why")
    for i, rec in enumerate(picks, start=1):
        gated = "*" if rec.spec.gated else ""
        table.add_row(
            str(i),
            f"{rec.spec.name}{gated}",
            rec.spec.params or f"{rec.spec.size_b}B",
            rec.spec.format[:4],
            f"{rec.required_gb:.0f}G",
            "; ".join(rec.reasons[:3]),
        )
    console.print(table)
    top = picks[0].spec.name
    console.print(
        f"\nTop pick: [bold cyan]{top}[/bold cyan]\n"
        f"Download: [green]ezra models download {top}[/green]"
    )


@main.command("init-config")
@click.option(
    "--home",
    "target",
    flag_value="home",
    default=True,
    help="Write ~/.ezra/ezra.yaml (default).",
)
@click.option(
    "--cwd",
    "target",
    flag_value="cwd",
    help="Write ./ezra.yaml in the current directory (gitignored at repo root).",
)
@click.option("--force", is_flag=True, help="Overwrite an existing ezra.yaml.")
@click.option(
    "--env",
    "with_env",
    is_flag=True,
    help="Also copy .env.example to .env in the current directory if missing.",
)
def init_config(target: str, force: bool, with_env: bool) -> None:
    """Copy the example config so you can customize paths and preferences.

    \b
    Examples:
      ezra init-config                 # ~/.ezra/ezra.yaml
      ezra init-config --cwd           # ./ezra.yaml (local; gitignored)
      ezra init-config --cwd --env     # also .env from .env.example
      ezra hpc init-site my-cluster    # HPC: partition / modules (commit & push)
    """
    import shutil

    from ezra.config import default_home
    from ezra.hpc.sites import repo_root

    root = repo_root()
    example = root / "ezra.yaml.example"
    if not example.is_file():
        example = Path(__file__).resolve().parent / "defaults" / "ezra.yaml"
    if not example.is_file():
        raise click.ClickException("Could not find ezra.yaml.example or packaged defaults.")

    if target == "cwd":
        dest = Path.cwd() / "ezra.yaml"
    else:
        dest = default_home() / "ezra.yaml"
        dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        raise click.ClickException(f"Already exists: {dest} (use --force to overwrite)")
    shutil.copyfile(example, dest)
    console.print(f"Wrote [bold]{dest}[/bold]")
    console.print("Edit it (search for EDIT ME), or set [green]EZRA_MODELS_DIR[/green].")
    console.print(
        "HPC clusters: [green]ezra hpc init-site my-cluster[/green] "
        "then [green]export EZRA_SITE=my-cluster[/green] (see sites/README.md)"
    )

    if with_env:
        env_ex = root / ".env.example"
        env_dest = Path.cwd() / ".env"
        if not env_ex.is_file():
            console.print("[yellow].env.example not found; skipped --env[/yellow]")
        elif env_dest.exists() and not force:
            console.print(f"[yellow]Skipped .env (already exists): {env_dest}[/yellow]")
        else:
            shutil.copyfile(env_ex, env_dest)
            console.print(f"Wrote [bold]{env_dest}[/bold] (gitignored - fill in tokens locally)")


@main.command("doctor")
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Quick environment check for HPC / local use."""
    from ezra.hardware import probe_system

    config = ctx.obj["config"]
    gallery: ModelGallery = ctx.obj["gallery"]
    site = os.environ.get("EZRA_SITE", "").strip() or "<none>"
    system = probe_system()
    console.print(f"EZRA version:     {__version__}")
    console.print(f"EZRA_SITE:        {site}")
    console.print(f"Models dir:       {config.models_dir}")
    console.print(
        "  (set with --models-dir PATH, EZRA_MODELS_DIR, or local.models_dir in ezra.yaml)"
    )
    console.print(f"Prefer quant:     {config.prefer_quant}")
    console.print(f"HF token env:     {config.hf_token_env}")
    console.print(f"HF token set:     {'yes' if config.hf_token else 'no'}")
    console.print(f"Gallery models:   {len(gallery.names())}")
    console.print(f"Max workers:      {config.max_workers}")
    console.print(f"CPU cores:        {system.cpu_count}")
    console.print(f"System RAM:       {system.ram_total_gb:.1f} GB")
    if system.gpus:
        gpu_bits = ", ".join(f"{g.name} ({g.vram_gb:.1f} GB)" for g in system.gpus)
        console.print(f"GPU:              {gpu_bits}")
        console.print(f"Fit budget:       {system.effective_memory_gb:.1f} GB (VRAM)")
    else:
        console.print("GPU:              none detected (nvidia-smi)")
        console.print(f"Fit budget:       {system.effective_memory_gb:.1f} GB (~80% RAM)")
    console.print(
        "Tip: [green]ezra models recommend chemistry[/green] "
        "picks open models that fit this machine"
    )
    if site == "<none>":
        console.print(
            "Tip: [green]ezra init-config[/green] (local) or "
            "[green]ezra hpc init-site my-cluster[/green] then "
            "[green]export EZRA_SITE=my-cluster[/green] (HPC - see sites/README.md)"
        )
    console.print(
        "Tip: [green]ezra agents init my-lab-assistant[/green] "
        "scaffolds a personal agent (prompt + preferred models)"
    )
    from ezra.gog import gog_root
    from ezra.gog import resolve_cli as resolve_gog_cli
    from ezra.inference.llama_cpp_engine import llama_cpp_available
    from ezra.inference.mlx_engine import mlx_available
    from ezra.openclaw import openclaw_root
    from ezra.openclaw import resolve_cli as resolve_openclaw_cli
    from ezra.parse import megaparse_available
    from ezra.peekaboo import (
        peekaboo_platform_supported,
        peekaboo_root,
        resolve_cli,
    )
    from ezra.serve import fastapi_available

    llama_status = (
        "[green]ok[/green]"
        if llama_cpp_available()
        else "[yellow]missing[/yellow] (pip install -e '.[local]')"
    )
    mlx_status = (
        "[green]ok[/green]"
        if mlx_available()
        else "[yellow]missing[/yellow] (pip install -e '.[mlx]')"
    )
    serve_status = (
        "[green]ok[/green]"
        if fastapi_available()
        else "[yellow]missing[/yellow] (pip install -e '.[serve]')"
    )
    parse_status = (
        "[green]ok[/green]"
        if megaparse_available()
        else "[yellow]basic only[/yellow] (pip install -e '.[parse]' · Python ≥ 3.11)"
    )
    cli_bin = resolve_cli()
    if not peekaboo_platform_supported():
        peekaboo_status = "[dim]n/a (macOS only)[/dim]"
    elif cli_bin is not None:
        peekaboo_status = f"[green]ok[/green] ({cli_bin})"
    elif peekaboo_root() is not None:
        peekaboo_status = (
            "[yellow]sources only[/yellow] "
            "(brew install steipete/tap/peekaboo or build third_party/Peekaboo)"
        )
    else:
        peekaboo_status = (
            "[yellow]missing[/yellow] "
            "(git submodule update --init --recursive third_party/Peekaboo)"
        )
    console.print(f"llama-cpp-python: {llama_status}")
    console.print(f"mlx-lm:           {mlx_status}")
    console.print(f"fastapi/uvicorn:  {serve_status}")
    console.print(f"MegaParse:        {parse_status}")
    gog_bin = resolve_gog_cli()
    if gog_bin is not None:
        gog_status = f"[green]ok[/green] ({gog_bin})"
    elif gog_root() is not None:
        gog_status = (
            "[yellow]sources only[/yellow] "
            "(brew install openclaw/tap/gogcli or make build in third_party/gogcli)"
        )
    else:
        gog_status = (
            "[yellow]missing[/yellow] "
            "(git submodule update --init third_party/gogcli)"
        )
    oc_bin = resolve_openclaw_cli()
    if oc_bin is not None:
        openclaw_status = f"[green]ok[/green] ({oc_bin})"
    elif openclaw_root() is not None:
        openclaw_status = (
            "[yellow]sources only[/yellow] "
            "(npm install -g openclaw@latest or build third_party/OpenClaw)"
        )
    else:
        openclaw_status = (
            "[yellow]missing[/yellow] "
            "(git submodule update --init --depth 1 third_party/OpenClaw)"
        )
    console.print(f"Peekaboo:         {peekaboo_status}")
    console.print(f"gog (Workspace):  {gog_status}")
    console.print(f"OpenClaw:         {openclaw_status}")
    console.print(f"Chat backend:     {config.backend}")
    console.print(f"Parse backend:    {config.parse_backend} / {config.parse_strategy}")
    console.print(f"Peekaboo enabled: {config.peekaboo_enabled}")
    console.print(f"gog enabled:      {config.gog_enabled}")
    console.print(f"OpenClaw enabled: {config.openclaw_enabled}")
    if config.gog_account:
        console.print(f"gog account:      {config.gog_account}")
    console.print(
        "Tip: [green]ezra chat --model qwen2.5-7b-instruct[/green] "
        "or [green]ezra serve --model qwen2.5-7b-instruct[/green]"
    )
    console.print(
        "Tip: [green]ezra parse paper.pdf -o paper.md[/green] "
        "or [green]ezra chat --file paper.pdf --model …[/green]"
    )
    console.print(
        "Tip: [green]ezra openclaw status[/green] "
        "(submodule pinned; EZRA never auto-starts the Gateway)"
    )
    try:
        config.models_dir.mkdir(parents=True, exist_ok=True)
        test = config.models_dir / ".ezra_write_test"
        test.write_text("ok", encoding="utf-8")
        test.unlink(missing_ok=True)
        console.print("Models dir write: [green]ok[/green]")
    except OSError as exc:
        console.print(f"Models dir write: [red]fail[/red] ({exc})")
        sys.exit(1)


@main.group("hpc")
def hpc_group() -> None:
    """Generate and submit SLURM SBATCH jobs (GPU / CPU / memory)."""


@hpc_group.command("templates")
def hpc_templates() -> None:
    """List built-in SBATCH job kinds and what they request."""
    from ezra.hpc.sbatch import JOB_KINDS, describe_kind, resources_from_config

    table = Table(title="EZRA SBATCH templates")
    table.add_column("Kind", style="cyan")
    table.add_column("GPUs")
    table.add_column("CPUs")
    table.add_column("Mem")
    table.add_column("Time")
    table.add_column("Purpose")
    for kind in JOB_KINDS:
        res = resources_from_config(kind)
        table.add_row(
            kind,
            str(res.gpus),
            str(res.cpus),
            res.mem,
            res.time,
            describe_kind(kind),
        )
    console.print(table)
    console.print(
        "\nCustomize for your HPC: [green]ezra hpc init-site my-cluster[/green] "
        "then [green]export EZRA_SITE=my-cluster[/green]\n"
        "Generate:  [green]ezra hpc script serve --model qwen2.5-7b-instruct[/green]\n"
        "Submit:    [green]ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1[/green]"
    )


@hpc_group.command("sites")
def hpc_sites() -> None:
    """List committed site profiles under sites/."""
    from ezra.hpc.sites import current_site, list_sites

    profiles = list_sites()
    active = os.environ.get("EZRA_SITE", "").strip() or None
    if not profiles:
        console.print("No site profiles yet (only the template).")
        console.print("Create one: [green]ezra hpc init-site my-cluster[/green]")
        console.print("Docs: [bold]sites/README.md[/bold]")
        return

    table = Table(title="EZRA site profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Active")
    table.add_column("Config")
    table.add_column("Modules")
    table.add_column("Path")
    for p in profiles:
        table.add_row(
            p.name,
            "yes" if active == p.name else "-",
            "yes" if p.config_path.is_file() else "missing",
            "yes" if p.modules_path.is_file() else "missing",
            str(p.path),
        )
    console.print(table)
    if active:
        try:
            site = current_site()
            console.print(f"EZRA_SITE=[bold]{site.name}[/bold] → {site.path}")
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]EZRA_SITE={active} invalid:[/red] {exc}")
    else:
        console.print("Set active profile: [green]export EZRA_SITE=<name>[/green]")


@hpc_group.command("init-site")
@click.argument("name")
@click.option("--force", is_flag=True, help="Overwrite an existing sites/<name> folder.")
@click.option(
    "--models-dir",
    type=click.Path(path_type=Path),
    default=None,
    help="Write this path into sites/<name>/ezra.yaml as local.models_dir.",
)
def hpc_init_site(name: str, force: bool, models_dir: Path | None) -> None:
    """Create sites/<name> from the editable template (then commit & push).

    \b
    Workflow:
      ezra hpc init-site frontier --models-dir /scratch/$USER/ezra/models
      $EDITOR sites/frontier/ezra.yaml      # EDIT ME: partition, account, gpus
      $EDITOR sites/frontier/modules.sh     # EDIT ME: module load …
      export EZRA_SITE=frontier
      git add sites/frontier && git commit && git push   # PR so others benefit
    """
    from ezra.hpc.sites import init_site

    try:
        profile = init_site(
            name,
            force=force,
            models_dir=str(models_dir.expanduser()) if models_dir is not None else None,
        )
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        raise click.ClickException(str(exc)) from exc

    console.print(f"Created site profile: [bold]{profile.path}[/bold]")
    if models_dir is not None:
        console.print(f"models_dir set to: [bold]{models_dir.expanduser()}[/bold]")
    console.print("1. Edit [cyan]ezra.yaml[/cyan] and [cyan]modules.sh[/cyan] (search for EDIT ME)")
    console.print("2. Fill in [cyan]NOTES.md[/cyan] for the next person on this cluster")
    console.print(f"3. [green]export EZRA_SITE={profile.name}[/green]")
    if models_dir is None:
        console.print(
            "4. Choose model storage, e.g. "
            "[green]export EZRA_MODELS_DIR=/scratch/$USER/ezra/models[/green]"
        )
        step = 5
    else:
        step = 4
    console.print(
        f"{step}. Commit & push (no secrets):\n"
        f"   [green]git checkout -b sites/{profile.name}[/green]\n"
        f"   [green]git add sites/{profile.name} && git commit -m "
        f"\"Add {profile.name} HPC site profile\"[/green]\n"
        f"   [green]git push -u origin sites/{profile.name}[/green]"
    )
    console.print("Details: [bold]sites/README.md[/bold]")


def _hpc_resources_options(fn):
    """Shared Click options for script / submit resource overrides."""
    opts = [
        click.option(
            "--models-dir",
            type=click.Path(path_type=Path),
            default=None,
            help="Directory for model weights (baked into script; also EZRA_MODELS_DIR).",
        ),
        click.option("--time", "walltime", default=None, help="Walltime, e.g. 08:00:00."),
        click.option("--cpus", type=int, default=None, help="CPUs per task."),
        click.option("--mem", default=None, help="Memory, e.g. 64G."),
        click.option("--gpus", type=int, default=None, help="GPU count (--gres=gpu:N)."),
        click.option("--gres", default=None, help="Full GRES string, e.g. gpu:a100:1."),
        click.option("--partition", default=None, help="SLURM partition / queue."),
        click.option("--account", default=None, help="SLURM account."),
        click.option("--qos", default=None, help="SLURM QoS."),
        click.option("--constraint", default=None, help="SLURM constraint (e.g. gpu type)."),
        click.option("--job-name", default=None, help="SLURM job name."),
    ]
    for opt in reversed(opts):
        fn = opt(fn)
    return fn


def _resolve_job_models_dir(ctx: click.Context, models_dir: Path | None) -> Path:
    """Resolve storage path for an HPC job (CLI flag > global config)."""
    if models_dir is not None:
        resolved = resolve_models_dir(cli_override=models_dir)
        ctx.obj["config"].models_dir = resolved
        return resolved
    return Path(ctx.obj["config"].models_dir)


def _apply_resource_overrides(ctx, kind, **kwargs):
    from ezra.hpc.sbatch import resources_from_config

    config = ctx.obj["config"]
    res = resources_from_config(kind, config.raw)
    return res.with_overrides(
        time=kwargs.get("walltime"),
        cpus=kwargs.get("cpus"),
        mem=kwargs.get("mem"),
        gpus=kwargs.get("gpus"),
        gres=kwargs.get("gres"),
        partition=kwargs.get("partition"),
        account=kwargs.get("account"),
        qos=kwargs.get("qos"),
        constraint=kwargs.get("constraint"),
        job_name=kwargs.get("job_name"),
    )


@hpc_group.command("script")
@click.argument("kind", type=click.Choice(["download", "serve", "interactive"]))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Write script to this path (default: stdout).",
)
@click.option("--model", default=None, help="Gallery model name (required for serve).")
@_hpc_resources_options
@click.pass_context
def hpc_script(
    ctx: click.Context,
    kind: str,
    output_path: Path | None,
    model: str | None,
    models_dir: Path | None,
    walltime: str | None,
    cpus: int | None,
    mem: str | None,
    gpus: int | None,
    gres: str | None,
    partition: str | None,
    account: str | None,
    qos: str | None,
    constraint: str | None,
    job_name: str | None,
) -> None:
    """Print or write an SBATCH script that requests GPUs/CPUs/memory.

    \b
    Examples:
      ezra hpc script download -o /tmp/ezra-dl.sh
      ezra hpc script download --models-dir /scratch/$USER/ezra/models -o /tmp/ezra-dl.sh
      ezra hpc script serve --model chemllm-7b --gpus 1 --mem 64G
      ezra hpc script interactive --gpus 1 --time 02:00:00
    """
    from ezra.hpc.sbatch import generate_script, write_script

    if kind == "serve" and not model:
        raise click.UsageError("serve requires --model <gallery-name>")

    job_models_dir = _resolve_job_models_dir(ctx, models_dir)
    res = _apply_resource_overrides(
        ctx,
        kind,
        walltime=walltime,
        cpus=cpus,
        mem=mem,
        gpus=gpus,
        gres=gres,
        partition=partition,
        account=account,
        qos=qos,
        constraint=constraint,
        job_name=job_name,
    )
    script = generate_script(
        kind,
        res,
        raw_config=ctx.obj["config"].raw,
        models_dir=job_models_dir,
    )

    if model:
        # Embed MODEL default so the script is self-contained when written to disk
        script = script.replace(
            'MODEL="${MODEL:?Set MODEL=<gallery-name> before sbatch (e.g. MODEL=qwen2.5-7b-instruct)}"',
            f'MODEL="${{MODEL:-{model}}}"',
            1,
        )
        script = script.replace('MODEL="${MODEL:-}"', f'MODEL="${{MODEL:-{model}}}"', 1)
        if kind == "download" and f'MODEL="${{MODEL:-{model}}}"' not in script:
            script = script.replace(
                'if [[ -n "${MODEL:-}" ]]; then',
                f'MODEL="${{MODEL:-{model}}}"\nif [[ -n "${{MODEL:-}}" ]]; then',
                1,
            )

    if output_path is None:
        click.echo(script)
    else:
        path = write_script(output_path, script)
        console.print(f"Wrote [bold]{path}[/bold]")
        console.print(f"Models dir: {job_models_dir}")
        if model:
            console.print(f"Submit: [green]MODEL={model} sbatch {path}[/green]")
        else:
            console.print(f"Submit: [green]sbatch {path}[/green]")


@hpc_group.command("submit")
@click.argument("kind", type=click.Choice(["download", "serve", "interactive"]))
@click.option("--model", default=None, help="Gallery model name (required for serve).")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the sbatch command without submitting.",
)
@click.option(
    "--sbatch-arg",
    "sbatch_args",
    multiple=True,
    help="Extra arg passed through to sbatch (repeatable).",
)
@_hpc_resources_options
@click.pass_context
def hpc_submit(
    ctx: click.Context,
    kind: str,
    model: str | None,
    dry_run: bool,
    sbatch_args: tuple[str, ...],
    models_dir: Path | None,
    walltime: str | None,
    cpus: int | None,
    mem: str | None,
    gpus: int | None,
    gres: str | None,
    partition: str | None,
    account: str | None,
    qos: str | None,
    constraint: str | None,
    job_name: str | None,
) -> None:
    """Generate an SBATCH script and submit it with sbatch.

    \b
    Examples:
      ezra hpc submit download --models-dir /scratch/$USER/ezra/models
      ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1 --cpus 8 --mem 64G
      ezra hpc submit interactive --gpus 1 --time 02:00:00 --dry-run
    """
    from ezra.hpc.sbatch import generate_script, submit_script

    if kind == "serve" and not model:
        raise click.UsageError("serve requires --model <gallery-name>")

    job_models_dir = _resolve_job_models_dir(ctx, models_dir)
    res = _apply_resource_overrides(
        ctx,
        kind,
        walltime=walltime,
        cpus=cpus,
        mem=mem,
        gpus=gpus,
        gres=gres,
        partition=partition,
        account=account,
        qos=qos,
        constraint=constraint,
        job_name=job_name,
    )
    script = generate_script(
        kind,
        res,
        raw_config=ctx.obj["config"].raw,
        models_dir=job_models_dir,
    )
    export_env: dict[str, str] = {
        "EZRA_MODELS_DIR": str(job_models_dir),
    }
    if model:
        export_env["MODEL"] = model
    site = os.environ.get("EZRA_SITE", "").strip()
    if site:
        export_env["EZRA_SITE"] = site

    try:
        result = submit_script(
            script,
            export_env=export_env or None,
            extra_sbatch_args=list(sbatch_args) or None,
            dry_run=dry_run,
        )
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    if dry_run:
        console.print(f"[yellow]dry-run[/yellow] {result}")
        console.print(f"Models dir: {job_models_dir}")
        console.print("Script preview (first lines):")
        console.print("\n".join(script.splitlines()[:16]))
    else:
        console.print(f"Submitted batch job [bold green]{result}[/bold green]")
        console.print(f"Models dir: {job_models_dir}")
        if model:
            console.print(f"MODEL={model}")


@main.group("agents")
def agents_group() -> None:
    """Scaffold and inspect personal agents (prompt + preferred models)."""


@agents_group.command("list")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def agents_list(as_json: bool) -> None:
    """List personal agent profiles under agents/."""
    from ezra.agents import list_agents, load_agent_spec

    profiles = list_agents()
    if as_json:
        rows = []
        for p in profiles:
            try:
                spec = load_agent_spec(p)
                rows.append(
                    {
                        "name": p.name,
                        "display_name": spec.name,
                        "description": spec.description,
                        "preferred": spec.preferred_models,
                        "path": str(p.path),
                    }
                )
            except (OSError, ValueError, TypeError) as exc:
                rows.append({"name": p.name, "path": str(p.path), "error": str(exc)})
        console.print_json(data=rows)
        return

    if not profiles:
        console.print("No agents yet. Create one with [green]ezra agents init NAME[/green]")
        console.print("Example: [cyan]ezra agents init my-lab-assistant[/cyan]")
        console.print("Starter: [cyan]agents/chem-assistant[/cyan] (see agents/README.md)")
        return

    table = Table(title="EZRA personal agents")
    table.add_column("Name", style="cyan")
    table.add_column("Preferred models")
    table.add_column("Focus")
    table.add_column("Description")
    for p in profiles:
        try:
            spec = load_agent_spec(p)
            preferred = ", ".join(spec.preferred_models[:3]) or "-"
            focus = ", ".join(spec.science_focus[:3]) or "-"
            desc = (spec.description[:60] + "…") if len(spec.description) > 60 else spec.description
            table.add_row(p.name, preferred, focus, desc or "-")
        except (OSError, ValueError, TypeError) as exc:
            table.add_row(p.name, "-", "-", f"[red]{exc}[/red]")
    console.print(table)


@agents_group.command("init")
@click.argument("name")
@click.option("--force", is_flag=True, help="Overwrite an existing agent folder.")
@click.option("--description", default=None, help="One-line description for agent.yaml.")
def agents_init(name: str, force: bool, description: str | None) -> None:
    """Create agents/<name> from the editable template (then customize).

    \b
    Examples:
      ezra agents init my-lab-assistant
      ezra agents init local/scratch-bot
      ezra agents init teaching-ta --description "Office-hours helper"
    """
    from ezra.agents import init_agent

    try:
        profile = init_agent(name, force=force, description=description)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        raise click.ClickException(str(exc)) from exc

    console.print(f"Created [bold]{profile.path}[/bold]")
    console.print("Edit [cyan]agent.yaml[/cyan] + [cyan]prompt.md[/cyan] (search for CUSTOMIZE ME).")
    console.print(f"Then: [green]ezra agents show {profile.name}[/green]")
    console.print(f"      [green]ezra agents check {profile.name}[/green]")
    if profile.name.startswith("local/"):
        console.print("[dim]agents/local/ is gitignored — fine for private experiments.[/dim]")
    else:
        console.print(
            "[dim]Optional: commit agents/"
            f"{profile.name} to share with your lab (no secrets).[/dim]"
        )


@agents_group.command("show")
@click.argument("name")
@click.option("--prompt", "show_prompt", is_flag=True, help="Print the full system prompt.")
def agents_show(name: str, show_prompt: bool) -> None:
    """Show one agent profile (models, prompt path, description)."""
    from ezra.agents import get_agent, load_agent_spec

    try:
        profile = get_agent(name)
        spec = load_agent_spec(profile)
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc

    console.print(f"[bold]{spec.name}[/bold]  ([cyan]{profile.name}[/cyan])")
    console.print(f"Path:         {profile.path}")
    if spec.description:
        console.print(f"Description:  {spec.description}")
    console.print(f"Preferred:    {', '.join(spec.preferred_models) or '(none)'}")
    console.print(f"Fallback:     {', '.join(spec.fallback_models) or '(none)'}")
    console.print(f"Model tags:   {', '.join(spec.model_tags) or '(none)'}")
    console.print(f"Focus:        {', '.join(spec.science_focus) or '(none)'}")
    console.print(f"Prompt file:  {profile.prompt_path}")
    if spec.router_mode:
        console.print(f"Router mode:  {spec.router_mode}")
    if profile.prompt_path.is_file():
        text = profile.prompt_path.read_text(encoding="utf-8")
        if show_prompt:
            console.print("\n-- prompt --")
            console.print(text.rstrip())
        else:
            preview = text.strip().splitlines()[:8]
            console.print("\n-- prompt preview --")
            console.print("\n".join(preview))
            if len(text.strip().splitlines()) > 8:
                console.print(f"[dim]... ({len(text.strip().splitlines())} lines; use --prompt)[/dim]")
    else:
        console.print(f"[yellow]Missing prompt file: {profile.prompt_path}[/yellow]")


@agents_group.command("check")
@click.argument("name")
@click.pass_context
def agents_check(ctx: click.Context, name: str) -> None:
    """Validate agent model aliases against the gallery and suggest downloads."""
    from ezra.agents import check_agent_models, get_agent, load_agent_spec

    gallery: ModelGallery = ctx.obj["gallery"]
    try:
        profile = get_agent(name)
        spec = load_agent_spec(profile)
    except (FileNotFoundError, ValueError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc

    result = check_agent_models(
        spec,
        gallery.names(),
        prompt_exists=profile.prompt_path.is_file(),
    )

    console.print(f"Agent [cyan]{profile.name}[/cyan] ({spec.name})")
    if result.known:
        console.print(f"Gallery OK:    [green]{', '.join(result.known)}[/green]")
    else:
        console.print("Gallery OK:    [yellow](no preferred/fallback aliases listed)[/yellow]")
    if result.unknown:
        console.print(f"Unknown:       [red]{', '.join(result.unknown)}[/red]")
        console.print("  Fix aliases in agent.yaml or add them to the gallery.")
    if result.missing_prompt:
        console.print(f"Prompt:        [red]missing[/red] ({profile.prompt_path})")
    else:
        console.print(f"Prompt:        [green]ok[/green] ({profile.prompt_path.name})")

    if result.download_hint:
        console.print(f"\nDownload: [green]{result.download_hint}[/green]")
    keyword = (spec.science_focus[0] if spec.science_focus else None) or (
        spec.model_tags[0] if spec.model_tags else None
    )
    if keyword and keyword != "general":
        console.print(
            f"Or pick by hardware: [green]ezra models recommend {keyword}[/green]"
        )
    else:
        console.print("Or pick by hardware: [green]ezra models recommend[/green]")

    if result.unknown or result.missing_prompt:
        sys.exit(1)


def _cli_backend(ctx: click.Context, backend: str):
    """Resolve chat backend from --backend flag."""
    from ezra.conversation import StubBackend
    from ezra.inference import create_backend

    config = ctx.obj["config"]
    prefer = backend.strip().lower()
    if prefer == "stub":
        return StubBackend(), "stub"
    try:
        runtime = create_backend(config, prefer=prefer, gallery=ctx.obj["gallery"])
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    label = getattr(runtime, "name", prefer)
    return runtime, str(label)


@main.command("parse")
@click.argument("path", type=click.Path(path_type=Path, exists=True))
@click.option(
    "--backend",
    "parse_backend",
    type=click.Choice(["auto", "basic", "megaparse"], case_sensitive=False),
    default=None,
    help="Parse backend (default: parse.backend from config).",
)
@click.option(
    "--strategy",
    type=click.Choice(["auto", "fast", "hi_res"], case_sensitive=False),
    default=None,
    help="MegaParse strategy (default: parse.strategy from config).",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=None,
    help="Write parsed text to this file (else stdout).",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON metadata + text.")
@click.pass_context
def parse_cmd(
    ctx: click.Context,
    path: Path,
    parse_backend: str | None,
    strategy: str | None,
    output: Path | None,
    as_json: bool,
) -> None:
    """Parse a document into LLM-ready text (MegaParse or basic).

    \b
    Examples:
      ezra parse notes.md
      ezra parse paper.pdf -o paper.md
      ezra parse slide.pptx --backend megaparse --strategy fast
    """
    from ezra.parse import DocumentParser

    config = ctx.obj["config"]
    backend = parse_backend or config.parse_backend
    strat = strategy or config.parse_strategy
    try:
        doc = DocumentParser(backend=backend, strategy=strat).parse(path)
    except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc

    if as_json:
        payload = {
            "path": str(doc.path),
            "backend": doc.backend,
            "strategy": doc.strategy,
            "file_type": doc.file_type,
            "metadata": doc.metadata,
            "text": doc.text,
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False)
    else:
        text = doc.text

    if output is not None:
        output = output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        console.print(
            f"Parsed [cyan]{doc.path.name}[/cyan] with "
            f"[magenta]{doc.backend}[/magenta] → [bold]{output}[/bold]"
        )
    else:
        console.print(text)


@main.command("chat")
@click.option("--agent", default=None, help="Personal agent under agents/<name>/.")
@click.option("--model", "model_name", default=None, help="Gallery model alias.")
@click.option(
    "--backend",
    "backend_name",
    type=click.Choice(["auto", "llama", "mlx", "stub"], case_sensitive=False),
    default="auto",
    show_default=True,
    help="Inference backend (stub = dry-run).",
)
@click.option("-p", "--prompt", "one_shot", default=None, help="One-shot prompt (non-interactive).")
@click.option(
    "--file",
    "doc_path",
    type=click.Path(path_type=Path, exists=True),
    default=None,
    help="Parse a document and prepend it to the first user message.",
)
@click.option("--stream/--no-stream", default=True, help="Stream tokens in the REPL.")
@click.pass_context
def chat_cmd(
    ctx: click.Context,
    agent: str | None,
    model_name: str | None,
    backend_name: str,
    one_shot: str | None,
    doc_path: Path | None,
    stream: bool,
) -> None:
    """Chat with a local model or personal agent.

    \b
    Examples:
      ezra chat --model qwen2.5-7b-instruct
      ezra chat --agent chem-assistant
      ezra chat --backend stub --model phi-3.5-mini-instruct -p "Hello"
      ezra chat --file paper.pdf --model qwen2.5-7b-instruct -p "Summarize methods"
    """
    from ezra.conversation import open_session
    from ezra.inference import BackendUnavailable, WeightsError

    if not agent and not model_name:
        raise click.UsageError("Provide --agent and/or --model")

    doc_prefix = ""
    if doc_path is not None:
        from ezra.parse import DocumentParser

        config = ctx.obj["config"]
        try:
            parsed = DocumentParser(
                backend=config.parse_backend,
                strategy=config.parse_strategy,
            ).parse(doc_path)
        except (FileNotFoundError, ValueError, RuntimeError, OSError) as exc:
            raise click.ClickException(str(exc)) from exc
        doc_prefix = parsed.as_chat_context() + "\n\n"

    backend, label = _cli_backend(ctx, backend_name)
    try:
        session = open_session(
            agent=agent,
            model=model_name,
            backend=backend,
            config=ctx.obj["config"],
        )
    except (BackendUnavailable, WeightsError, FileNotFoundError, ValueError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc

    def _banner() -> None:
        who = f"agent={session.agent}" if session.agent else "no agent"
        console.print(
            f"[bold]EZRA chat[/bold]  model=[cyan]{session.model}[/cyan]  "
            f"{who}  backend=[magenta]{label}[/magenta]"
        )
        if doc_path is not None:
            console.print(f"[dim]Document context: {doc_path}[/dim]")
        console.print("[dim]Commands: /save  /quit[/dim]")

    if one_shot is not None:
        prompt = doc_prefix + one_shot
        if stream:
            console.print(f"[dim]({session.model})[/dim] ", end="")
            for chunk in session.stream(prompt):
                console.print(chunk, end="")
            console.print()
        else:
            reply = session.send(prompt)
            console.print(f"[dim]({reply.model}{f' / {reply.agent}' if reply.agent else ''})[/dim]")
            console.print(reply.text)
        return

    _banner()
    first = True
    while True:
        try:
            line = console.input("[bold green]you>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            break
        if not line:
            continue
        if line in {"/quit", "/exit", ":q"}:
            break
        if line == "/save":
            path = session.save()
            console.print(f"Saved [bold]{path}[/bold]")
            continue
        try:
            user_text = (doc_prefix + line) if first and doc_prefix else line
            first = False
            if stream:
                console.print(f"[bold cyan]{session.model}>[/bold cyan] ", end="")
                for chunk in session.stream(user_text):
                    console.print(chunk, end="")
                console.print()
            else:
                reply = session.send(user_text)
                tag = reply.model
                if reply.agent:
                    tag = f"{reply.agent} / {reply.model}"
                console.print(f"[bold cyan]{tag}>[/bold cyan] {reply.text}")
        except (BackendUnavailable, WeightsError, RuntimeError, OSError) as exc:
            console.print(f"[red]{exc}[/red]")


@main.command("serve")
@click.option("--agent", default=None, help="Default agent for requests without model=agent:…")
@click.option("--model", "model_name", default=None, help="Default gallery model.")
@click.option(
    "--backend",
    "backend_name",
    type=click.Choice(["auto", "llama", "mlx", "stub"], case_sensitive=False),
    default="auto",
    show_default=True,
)
@click.option("--host", default=None, help="Bind host (default 0.0.0.0 or EZRA_HOST).")
@click.option("--port", default=None, type=int, help="Bind port (default 8000 or EZRA_PORT).")
@click.pass_context
def serve_cmd(
    ctx: click.Context,
    agent: str | None,
    model_name: str | None,
    backend_name: str,
    host: str | None,
    port: int | None,
) -> None:
    """OpenAI-compatible HTTP API (``/v1/chat/completions``).

    \b
    Examples:
      ezra serve --model qwen2.5-7b-instruct --port 8000
      ezra serve --agent chem-assistant --backend stub
    """
    from ezra.serve import create_app, fastapi_available, run_server

    if not fastapi_available():
        raise click.ClickException(
            "FastAPI/uvicorn not installed. Install with: pip install -e '.[serve]'"
        )
    if not agent and not model_name:
        raise click.UsageError(
            "Provide --agent and/or --model as the default for this server."
        )

    backend, label = _cli_backend(ctx, backend_name)
    bind_host = host or os.environ.get("EZRA_HOST", "0.0.0.0")
    bind_port = int(port or os.environ.get("EZRA_PORT", "8000"))

    app = create_app(
        backend=backend,
        default_agent=agent,
        default_model=model_name,
        gallery=ctx.obj["gallery"],
        backend_label=label,
        config=ctx.obj["config"],
    )
    console.print(
        f"Serving OpenAI API on [bold]http://{bind_host}:{bind_port}/v1[/bold]  "
        f"(backend=[magenta]{label}[/magenta])"
    )
    run_server(app, host=bind_host, port=bind_port)


@main.group("peekaboo")
def peekaboo_group() -> None:
    """macOS Peekaboo helpers (vendored under third_party/Peekaboo)."""


@peekaboo_group.command("status")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
@click.pass_context
def peekaboo_status(ctx: click.Context, as_json: bool) -> None:
    """Show Peekaboo submodule / CLI availability."""
    from ezra.peekaboo import (
        mcp_launch_command,
        peekaboo_available,
        peekaboo_platform_supported,
        peekaboo_root,
        resolve_cli,
    )

    config = ctx.obj["config"]
    root = peekaboo_root()
    cli_bin = resolve_cli()
    payload = {
        "enabled": config.peekaboo_enabled,
        "platform_supported": peekaboo_platform_supported(),
        "available": peekaboo_available(),
        "root": str(root) if root else None,
        "cli": str(cli_bin) if cli_bin else None,
        "cli_override": config.peekaboo_cli or None,
        "mcp_launch": mcp_launch_command(),
        "upstream": "https://github.com/openclaw/Peekaboo",
    }
    if as_json:
        console.print(json.dumps(payload, indent=2))
        return
    console.print(f"Enabled:     {payload['enabled']}")
    console.print(f"Platform:    {'macOS' if payload['platform_supported'] else 'other (CLI n/a)'}")
    console.print(f"Available:   {'yes' if payload['available'] else 'no'}")
    console.print(f"Submodule:   {payload['root'] or '<missing — git submodule update --init --recursive>'}")
    console.print(f"CLI:         {payload['cli'] or '<not found on PATH / build tree>'}")
    console.print(f"MCP launch:  {' '.join(payload['mcp_launch'])}")
    console.print(f"Upstream:    {payload['upstream']}")


@peekaboo_group.command("mcp-config")
@click.option("--npx", "prefer_npx", is_flag=True, help="Prefer npx @steipete/peekaboo.")
def peekaboo_mcp_config(prefer_npx: bool) -> None:
    """Print a Cursor / Claude MCP snippet for Peekaboo."""
    from ezra.peekaboo import mcp_launch_command

    argv = mcp_launch_command(prefer_npx=prefer_npx)
    snippet = {
        "mcpServers": {
            "peekaboo": {
                "command": argv[0],
                "args": argv[1:],
            }
        }
    }
    console.print(json.dumps(snippet, indent=2))


@peekaboo_group.command("capture")
@click.option(
    "--path",
    "out_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output PNG (default: ~/.ezra/captures/...).",
)
@click.option(
    "--mode",
    default="screen",
    show_default=True,
    help="Peekaboo image mode (e.g. screen).",
)
def peekaboo_capture(out_path: Path | None, mode: str) -> None:
    """Capture the screen via Peekaboo (macOS + CLI required)."""
    from ezra.peekaboo import PeekabooNotAvailable, capture_screen

    try:
        saved = capture_screen(out_path, mode=mode)
    except PeekabooNotAvailable as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:
        raise click.ClickException(f"Peekaboo capture failed: {exc}") from exc
    console.print(f"Saved [cyan]{saved}[/cyan]")


@main.group("gog")
def gog_group() -> None:
    """Google Workspace helpers via gogcli (vendored under third_party/gogcli)."""


@gog_group.command("status")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
@click.pass_context
def gog_status(ctx: click.Context, as_json: bool) -> None:
    """Show gogcli submodule / CLI availability."""
    from ezra.gog import gog_available, gog_root, mcp_launch_command, resolve_cli

    config = ctx.obj["config"]
    root = gog_root()
    cli_bin = resolve_cli()
    payload = {
        "enabled": config.gog_enabled,
        "available": gog_available(),
        "root": str(root) if root else None,
        "cli": str(cli_bin) if cli_bin else None,
        "cli_override": config.gog_cli or None,
        "account": config.gog_account or None,
        "mcp_launch": mcp_launch_command(),
        "upstream": "https://github.com/openclaw/gogcli",
    }
    if as_json:
        console.print(json.dumps(payload, indent=2))
        return
    console.print(f"Enabled:     {payload['enabled']}")
    console.print(f"Available:   {'yes' if payload['available'] else 'no'}")
    console.print(
        f"Submodule:   {payload['root'] or '<missing — git submodule update --init>'}"
    )
    console.print(f"CLI:         {payload['cli'] or '<not found on PATH / build tree>'}")
    console.print(f"Account:     {payload['account'] or '<unset — GOG_ACCOUNT>'}")
    console.print(f"MCP launch:  {' '.join(payload['mcp_launch'])}")
    console.print(f"Upstream:    {payload['upstream']}")


@gog_group.command("mcp-config")
def gog_mcp_config() -> None:
    """Print a Cursor / Claude MCP snippet for gog."""
    from ezra.gog import mcp_launch_command

    argv = mcp_launch_command()
    snippet = {
        "mcpServers": {
            "gog": {
                "command": argv[0],
                "args": argv[1:],
            }
        }
    }
    console.print(json.dumps(snippet, indent=2))


@gog_group.command(
    "run",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option(
    "--readonly/--no-readonly",
    default=True,
    help="Pass --readonly to gog (default: on).",
)
@click.pass_context
def gog_run(ctx: click.Context, readonly: bool) -> None:
    """Forward args to ``gog`` (default --readonly for safer agent use).

    \b
    Examples:
      ezra gog run gmail search 'newer_than:7d' --max 5 --json
      ezra gog run --no-readonly calendar events --today
    """
    from ezra.gog import GogNotAvailable, run_gog

    args = list(ctx.args)
    if not args:
        raise click.UsageError("Pass a gog subcommand, e.g. gmail search '…'")
    try:
        result = run_gog(*args, readonly=readonly, check=False, capture_output=False)
    except GogNotAvailable as exc:
        raise click.ClickException(str(exc)) from exc
    if result.returncode:
        sys.exit(result.returncode)


@main.group("openclaw")
def openclaw_group() -> None:
    """OpenClaw helpers (pinned submodule under third_party/OpenClaw).

    Safe by default: status/version only. Does not run onboard or start Gateway.
    """


@openclaw_group.command("status")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
@click.pass_context
def openclaw_status_cmd(ctx: click.Context, as_json: bool) -> None:
    """Show OpenClaw submodule / CLI availability (no Gateway start)."""
    from ezra.openclaw import (
        openclaw_available,
        openclaw_pin_info,
        openclaw_root,
        openclaw_version,
        resolve_cli,
    )

    config = ctx.obj["config"]
    root = openclaw_root()
    cli_bin = resolve_cli()
    pin = openclaw_pin_info(root)
    payload = {
        "enabled": config.openclaw_enabled,
        "available": openclaw_available(),
        "root": str(root) if root else None,
        "cli": str(cli_bin) if cli_bin else None,
        "cli_override": config.openclaw_cli or None,
        "pin": pin,
        "version_probe": openclaw_version() if cli_bin else None,
        "auto_start": False,
        "note": "EZRA never auto-runs onboard or starts the Gateway",
    }
    if as_json:
        console.print(json.dumps(payload, indent=2))
        return
    console.print(f"Enabled:     {payload['enabled']}")
    console.print(f"Available:   {'yes' if payload['available'] else 'no'}")
    console.print(
        f"Submodule:   {payload['root'] or '<missing — git submodule update --init --depth 1 third_party/OpenClaw>'}"
    )
    console.print(f"CLI:         {payload['cli'] or '<not found — npm install -g openclaw@latest>'}")
    if pin.get("version"):
        console.print(f"Pin version: {pin['version']}")
    if payload["version_probe"]:
        console.print(f"CLI version: {payload['version_probe']}")
    console.print(f"Upstream:    {pin.get('upstream')}")
    console.print("[dim]Auto-start Gateway: no (by design)[/dim]")


@openclaw_group.command("version")
def openclaw_version_cmd() -> None:
    """Probe ``openclaw --version`` if a CLI is resolvable."""
    from ezra.openclaw import OpenClawNotAvailable, openclaw_version, run_openclaw

    ver = openclaw_version()
    if ver:
        console.print(ver)
        return
    try:
        proc = run_openclaw("--version", check=False)
    except OpenClawNotAvailable as exc:
        raise click.ClickException(str(exc)) from exc
    text = (proc.stdout or proc.stderr or "").strip() or "<no output>"
    console.print(text)
    if proc.returncode:
        sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
