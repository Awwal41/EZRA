"""EZRA command-line interface (HPC / laptop)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ezra import __version__
from ezra.config import load_config
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
    help="Override model storage directory (also: EZRA_MODELS_DIR).",
)
@click.pass_context
def main(ctx: click.Context, config_path: Path | None, models_dir: Path | None) -> None:
    """EZRA — Easy Zero-setup Routing Assistant for local & HPC LLMs."""
    ctx.ensure_object(dict)
    config = load_config(config_path)
    if models_dir is not None:
        config.models_dir = models_dir.expanduser().resolve()
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
        tags = ",".join(list(s.science_tags)[:2] or list(s.tags)[:2]) or "—"
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
        f"\nModels dir: [bold]{ctx.obj['config'].models_dir}[/bold]"
        "  (* = gated HF license)\n"
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
        if result.status == "failed":
            sys.exit(1)


@main.command("doctor")
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Quick environment check for HPC / local use."""
    config = ctx.obj["config"]
    gallery: ModelGallery = ctx.obj["gallery"]
    console.print(f"EZRA version:     {__version__}")
    console.print(f"Models dir:       {config.models_dir}")
    console.print(f"Prefer quant:     {config.prefer_quant}")
    console.print(f"HF token env:     {config.hf_token_env}")
    console.print(f"HF token set:     {'yes' if config.hf_token else 'no'}")
    console.print(f"Gallery models:   {len(gallery.names())}")
    console.print(f"Max workers:      {config.max_workers}")
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
        "\nGenerate:  [green]ezra hpc script serve --model qwen2.5-7b-instruct[/green]\n"
        "Submit:    [green]ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1[/green]"
    )


def _hpc_resources_options(fn):
    """Shared Click options for script / submit resource overrides."""
    opts = [
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
      ezra hpc script serve --model chemllm-7b --gpus 1 --mem 64G
      ezra hpc script interactive --gpus 1 --time 02:00:00
    """
    from ezra.hpc.sbatch import generate_script, write_script

    if kind == "serve" and not model:
        raise click.UsageError("serve requires --model <gallery-name>")

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
    script = generate_script(kind, res, raw_config=ctx.obj["config"].raw)

    if model:
        # Embed MODEL default so the script is self-contained when written to disk
        script = script.replace(
            'MODEL="${MODEL:?Set MODEL=<gallery-name> before sbatch (e.g. MODEL=qwen2.5-7b-instruct)}"',
            f'MODEL="${{MODEL:-{model}}}"',
            1,
        )
        if kind == "interactive":
            script = script.replace('MODEL="${MODEL:-}"', f'MODEL="${{MODEL:-{model}}}"', 1)

    if output_path is None:
        click.echo(script)
    else:
        path = write_script(output_path, script)
        console.print(f"Wrote [bold]{path}[/bold]")
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
      ezra hpc submit download --max-size style via env: MAX_SIZE=8
      ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1 --cpus 8 --mem 64G
      ezra hpc submit interactive --gpus 1 --time 02:00:00 --dry-run
    """
    from ezra.hpc.sbatch import generate_script, submit_script

    if kind == "serve" and not model:
        raise click.UsageError("serve requires --model <gallery-name>")

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
    script = generate_script(kind, res, raw_config=ctx.obj["config"].raw)
    export_env: dict[str, str] = {}
    if model:
        export_env["MODEL"] = model
    models_dir = ctx.obj["config"].models_dir
    export_env["EZRA_MODELS_DIR"] = str(models_dir)

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
        console.print("Script preview (first lines):")
        console.print("\n".join(script.splitlines()[:16]))
    else:
        console.print(f"Submitted batch job [bold green]{result}[/bold green]")
        console.print(f"Models dir: {models_dir}")
        if model:
            console.print(f"MODEL={model}")


if __name__ == "__main__":
    main()
