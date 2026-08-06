"""Generate and submit SLURM SBATCH scripts for EZRA jobs.

Jobs request CPUs, memory, walltime, and (for serve/interactive) GPUs so
inference can run on compute nodes rather than the login node.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

JobKind = Literal["download", "serve", "interactive"]

JOB_KINDS: tuple[JobKind, ...] = ("download", "serve", "interactive")

# Sensible defaults when ezra.yaml has no hpc.slurm section
_DEFAULTS: dict[JobKind, dict[str, Any]] = {
    "download": {
        "job_name": "ezra-download",
        "time": "04:00:00",
        "cpus": 4,
        "mem": "8G",
        "gpus": 0,
    },
    "serve": {
        "job_name": "ezra-serve",
        "time": "08:00:00",
        "cpus": 8,
        "mem": "64G",
        "gpus": 1,
    },
    "interactive": {
        "job_name": "ezra-interactive",
        "time": "02:00:00",
        "cpus": 4,
        "mem": "32G",
        "gpus": 1,
    },
}


@dataclass
class SlurmResources:
    """SLURM resource request used to emit #SBATCH directives."""

    job_name: str = "ezra"
    time: str = "04:00:00"
    cpus: int = 4
    mem: str = "8G"
    gpus: int = 0
    gres: str | None = None
    partition: str | None = None
    account: str | None = None
    qos: str | None = None
    nodes: int = 1
    output: str | None = None
    error: str | None = None
    constraint: str | None = None
    extra: list[str] = field(default_factory=list)

    def with_overrides(
        self,
        *,
        time: str | None = None,
        cpus: int | None = None,
        mem: str | None = None,
        gpus: int | None = None,
        gres: str | None = None,
        partition: str | None = None,
        account: str | None = None,
        qos: str | None = None,
        job_name: str | None = None,
        constraint: str | None = None,
    ) -> SlurmResources:
        """Return a copy with any non-None fields replaced."""
        kwargs: dict[str, Any] = {}
        if time is not None:
            kwargs["time"] = time
        if cpus is not None:
            kwargs["cpus"] = cpus
        if mem is not None:
            kwargs["mem"] = mem
        if gpus is not None:
            kwargs["gpus"] = gpus
        if gres is not None:
            kwargs["gres"] = gres
        if partition is not None:
            kwargs["partition"] = partition
        if account is not None:
            kwargs["account"] = account
        if qos is not None:
            kwargs["qos"] = qos
        if job_name is not None:
            kwargs["job_name"] = job_name
        if constraint is not None:
            kwargs["constraint"] = constraint
        return replace(self, **kwargs) if kwargs else self


def resources_from_config(
    kind: JobKind,
    raw: dict[str, Any] | None = None,
) -> SlurmResources:
    """Build SlurmResources from ezra.yaml ``hpc.slurm`` (plus kind defaults)."""
    base = dict(_DEFAULTS[kind])
    hpc = (raw or {}).get("hpc") or {}
    slurm = hpc.get("slurm") or {}
    kind_cfg = slurm.get(kind) or {}

    # Global defaults apply first; per-kind overrides win
    merged: dict[str, Any] = {**base}
    for key in ("partition", "account", "qos", "constraint"):
        if slurm.get(key):
            merged[key] = slurm[key]
    merged.update({k: v for k, v in kind_cfg.items() if v is not None})

    gpus = int(merged.get("gpus", 0))
    gres = merged.get("gres")
    if gres is None and gpus > 0:
        gres = f"gpu:{gpus}"

    return SlurmResources(
        job_name=str(merged.get("job_name", f"ezra-{kind}")),
        time=str(merged.get("time", "04:00:00")),
        cpus=int(merged.get("cpus", 4)),
        mem=str(merged.get("mem", "8G")),
        gpus=gpus,
        gres=str(gres) if gres else None,
        partition=_opt_str(merged.get("partition")),
        account=_opt_str(merged.get("account")),
        qos=_opt_str(merged.get("qos")),
        nodes=int(merged.get("nodes", 1)),
        constraint=_opt_str(merged.get("constraint")),
        extra=list(merged.get("extra") or []),
    )


def _opt_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def render_sbatch_header(res: SlurmResources) -> str:
    """Emit the #!/usr/bin/env bash + #SBATCH resource block."""
    out = res.output or f"{res.job_name}-%j.out"
    err = res.error or f"{res.job_name}-%j.err"
    lines = [
        "#!/usr/bin/env bash",
        f"#SBATCH --job-name={res.job_name}",
        f"#SBATCH --output={out}",
        f"#SBATCH --error={err}",
        f"#SBATCH --time={res.time}",
        f"#SBATCH --nodes={res.nodes}",
        f"#SBATCH --cpus-per-task={res.cpus}",
        f"#SBATCH --mem={res.mem}",
    ]
    if res.gres:
        lines.append(f"#SBATCH --gres={res.gres}")
    elif res.gpus > 0:
        lines.append(f"#SBATCH --gres=gpu:{res.gpus}")
    if res.partition:
        lines.append(f"#SBATCH --partition={res.partition}")
    if res.account:
        lines.append(f"#SBATCH --account={res.account}")
    if res.qos:
        lines.append(f"#SBATCH --qos={res.qos}")
    if res.constraint:
        lines.append(f"#SBATCH --constraint={res.constraint}")
    for item in res.extra:
        item = item.strip()
        if not item:
            continue
        if item.startswith("#SBATCH"):
            lines.append(item)
        else:
            lines.append(f"#SBATCH {item}")
    return "\n".join(lines)


def _repo_bootstrap() -> str:
    return r"""
set -euo pipefail

# Prefer project/scratch storage on HPC
export EZRA_MODELS_DIR="${EZRA_MODELS_DIR:-${SCRATCH:-$HOME}/ezra/models}"
export EZRA_HOME="${EZRA_HOME:-${SCRATCH:-$HOME}/ezra}"
mkdir -p "$EZRA_MODELS_DIR" "$EZRA_HOME"

# Resolve repo root when submitted from a git checkout; else use EZRA_ROOT
if [[ -n "${EZRA_ROOT:-}" ]]; then
  ROOT="$EZRA_ROOT"
elif [[ -n "${SLURM_SUBMIT_DIR:-}" && -f "${SLURM_SUBMIT_DIR}/pyproject.toml" ]]; then
  ROOT="$SLURM_SUBMIT_DIR"
else
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
cd "$ROOT"

# ── Site profile (EDIT / create with: ezra hpc init-site <name>) ─────────
# export EZRA_SITE=my-cluster
if [[ -n "${EZRA_SITE:-}" ]]; then
  SITE_DIR="$ROOT/sites/$EZRA_SITE"
  if [[ ! -d "$SITE_DIR" ]]; then
    echo "EZRA_SITE=$EZRA_SITE but missing directory: $SITE_DIR" >&2
    echo "Create one: ezra hpc init-site $EZRA_SITE" >&2
    exit 1
  fi
  if [[ -f "$SITE_DIR/ezra.yaml" ]]; then
    export EZRA_CONFIG="${EZRA_CONFIG:-$SITE_DIR/ezra.yaml}"
    echo "Using site config: $EZRA_CONFIG"
  fi
  if [[ -f "$SITE_DIR/modules.sh" ]]; then
    echo "Sourcing site modules: $SITE_DIR/modules.sh"
    # shellcheck disable=SC1090
    source "$SITE_DIR/modules.sh"
  fi
else
  echo "Tip: set EZRA_SITE=<name> after 'ezra hpc init-site <name>' so partition/modules match your HPC."
  # Fallback when no site profile — EDIT ME for a one-off, or use a site profile instead:
  # module load python/3.11
  # module load cuda/12.4
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -U pip
pip install -q -e .

echo "=== EZRA job on $(hostname) ==="
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>}"
echo "SLURM_JOB_ID=${SLURM_JOB_ID:-<none>}  GPUS=${SLURM_GPUS:-${SLURM_GPUS_ON_NODE:-0}}"
echo "EZRA_SITE=${EZRA_SITE:-<none>}"
ezra doctor
command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi || true
""".strip()


def _body_download() -> str:
    return r"""
if [[ -n "${MODEL:-}" ]]; then
  echo "Downloading single model: $MODEL"
  ezra models download "$MODEL" --workers "${EZRA_WORKERS:-2}"
else
  echo "Downloading all free (non-gated) models under ${MAX_SIZE:-14}B..."
  ezra models download --all --no-gated --max-size "${MAX_SIZE:-14}" --workers "${EZRA_WORKERS:-2}"
fi

ezra models status
""".strip()


def _body_serve() -> str:
    return r"""
MODEL="${MODEL:?Set MODEL=<gallery-name> before sbatch (e.g. MODEL=qwen2.5-7b-instruct)}"
HOST="${EZRA_HOST:-0.0.0.0}"
PORT="${EZRA_PORT:-8000}"

echo "Serving model: $MODEL on ${HOST}:${PORT}"
ezra models info "$MODEL" || {
  echo "Model not installed. Download first, e.g.:"
  echo "  MODEL=$MODEL sbatch scripts/hpc_download_all.sh"
  exit 1
}

# OpenAI-compatible local API (llama.cpp / MLX / vLLM backends).
# Until backends ship, this still reserves the GPU node and fails clearly.
if ezra serve --help >/dev/null 2>&1; then
  exec ezra serve --model "$MODEL" --host "$HOST" --port "$PORT"
else
  echo "ezra serve is not available in this build yet."
  echo "GPU/CPU allocation succeeded — install an inference backend, then re-submit."
  echo "Holding allocation briefly so you can attach / debug (CTRL+C or scancel to stop)."
  sleep "${EZRA_HOLD_SECONDS:-300}"
fi
""".strip()


def _body_interactive() -> str:
    return r"""
MODEL="${MODEL:-}"
echo "Interactive EZRA allocation ready on $(hostname)."
echo "Useful next steps inside this job (or after srun --jobid=... --pty bash):"
echo "  export EZRA_MODELS_DIR=$EZRA_MODELS_DIR"
if [[ -n "$MODEL" ]]; then
  echo "  ezra models info $MODEL"
  echo "  ezra serve --model $MODEL --host 0.0.0.0 --port \${EZRA_PORT:-8000}"
else
  echo "  ezra models list"
  echo "  ezra models download <name>"
fi
echo "Sleeping so the allocation stays up (override with EZRA_HOLD_SECONDS)."
sleep "${EZRA_HOLD_SECONDS:-7200}"
""".strip()


_BODIES = {
    "download": _body_download,
    "serve": _body_serve,
    "interactive": _body_interactive,
}

_DESCRIPTIONS = {
    "download": "CPU job: stage gallery weights onto shared storage (no GPU).",
    "serve": "GPU job: run OpenAI-compatible ezra serve for one installed model.",
    "interactive": "GPU job: hold a node for manual ezra / debug / srun attach.",
}


def describe_kind(kind: JobKind) -> str:
    return _DESCRIPTIONS[kind]


def generate_script(
    kind: JobKind,
    resources: SlurmResources | None = None,
    *,
    raw_config: dict[str, Any] | None = None,
    header_comment: str | None = None,
) -> str:
    """Return a complete SBATCH script for ``kind``."""
    if kind not in JOB_KINDS:
        raise ValueError(f"Unknown job kind {kind!r}; choose from {JOB_KINDS}")
    res = resources or resources_from_config(kind, raw_config)
    comment = header_comment or {
        "download": "EZRA SLURM job: download curated free models (CPU).",
        "serve": "EZRA SLURM job: serve a model with GPU/CPU allocation.",
        "interactive": "EZRA SLURM job: interactive GPU allocation for EZRA.",
    }[kind]
    usage = {
        "download": (
            "# Usage:\n"
            "#   sbatch scripts/hpc_download_all.sh\n"
            "#   MODEL=qwen2.5-7b-instruct sbatch <this-script>\n"
            "#   ezra hpc submit download\n"
        ),
        "serve": (
            "# Usage:\n"
            "#   MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_serve_gpu.sh\n"
            "#   ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1\n"
        ),
        "interactive": (
            "# Usage:\n"
            "#   sbatch scripts/hpc_interactive.sh\n"
            "#   ezra hpc submit interactive --gpus 1 --time 02:00:00\n"
        ),
    }[kind]
    parts = [
        render_sbatch_header(res),
        "",
        f"# {comment}",
        usage.rstrip(),
        "",
        _repo_bootstrap(),
        "",
        _BODIES[kind](),
        "",
    ]
    return "\n".join(parts)


def write_script(path: Path, script: str) -> Path:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script, encoding="utf-8", newline="\n")
    try:
        path.chmod(path.stat().st_mode | 0o755)
    except OSError:
        pass
    return path


def submit_script(
    script: str | Path,
    *,
    export_env: dict[str, str] | None = None,
    extra_sbatch_args: list[str] | None = None,
    dry_run: bool = False,
) -> str:
    """Submit a script via ``sbatch``. Returns job id (or dry-run command).

    Raises ``FileNotFoundError`` if ``sbatch`` is not on PATH.
    Raises ``RuntimeError`` if sbatch exits non-zero.
    """
    sbatch = shutil.which("sbatch")
    if sbatch is None and not dry_run:
        raise FileNotFoundError(
            "sbatch not found on PATH. Generate a script with "
            "`ezra hpc script ...` and submit on a SLURM login node."
        )

    tmp_path: Path | None = None
    if isinstance(script, Path) or (
        isinstance(script, str) and "\n" not in script and Path(script).is_file()
    ):
        script_path = Path(script)
    elif dry_run:
        script_path = Path("<generated-ezra.sbatch.sh>")
    else:
        fd, name = tempfile.mkstemp(prefix="ezra-", suffix=".sbatch.sh", text=True)
        os.close(fd)
        tmp_path = Path(name)
        write_script(tmp_path, str(script))
        script_path = tmp_path

    env = os.environ.copy()
    if export_env:
        env.update({k: str(v) for k, v in export_env.items() if v is not None})

    # Pass through MODEL / EZRA_* via --export so batch jobs see them
    export_keys = ["ALL"]
    if export_env:
        export_keys.extend(f"{k}={v}" for k, v in export_env.items())
    cmd = [sbatch or "sbatch", f"--export={','.join(export_keys)}"]
    if extra_sbatch_args:
        cmd.extend(extra_sbatch_args)
    cmd.append(str(script_path))

    if dry_run:
        return " ".join(cmd)

    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"sbatch failed ({proc.returncode}): {err}")

    out = (proc.stdout or "").strip()
    # Typical: "Submitted batch job 12345"
    job_id = out.split()[-1] if out else ""
    return job_id or out
