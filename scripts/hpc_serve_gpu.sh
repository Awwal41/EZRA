#!/usr/bin/env bash
#SBATCH --job-name=ezra-serve
#SBATCH --output=ezra-serve-%j.out
#SBATCH --error=ezra-serve-%j.err
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
# ── EDIT ME (or use a site profile instead of editing this file) ──────────
# #SBATCH --partition=gpu
# #SBATCH --account=mylab
# #SBATCH --constraint=a100
#
# Preferred: ezra hpc init-site my-cluster && export EZRA_SITE=my-cluster
# See sites/README.md

# EZRA SLURM job: serve a model with GPU/CPU allocation.
# Usage:
#   export EZRA_SITE=my-cluster
#   MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_serve_gpu.sh
#   ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1

set -euo pipefail

export EZRA_MODELS_DIR="${EZRA_MODELS_DIR:-${SCRATCH:-$HOME}/ezra/models}"
export EZRA_HOME="${EZRA_HOME:-${SCRATCH:-$HOME}/ezra}"
mkdir -p "$EZRA_MODELS_DIR" "$EZRA_HOME"

if [[ -n "${EZRA_ROOT:-}" ]]; then
  ROOT="$EZRA_ROOT"
elif [[ -n "${SLURM_SUBMIT_DIR:-}" && -f "${SLURM_SUBMIT_DIR}/pyproject.toml" ]]; then
  ROOT="$SLURM_SUBMIT_DIR"
else
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
cd "$ROOT"

if [[ -n "${EZRA_SITE:-}" ]]; then
  SITE_DIR="$ROOT/sites/$EZRA_SITE"
  if [[ ! -d "$SITE_DIR" ]]; then
    echo "EZRA_SITE=$EZRA_SITE but missing directory: $SITE_DIR" >&2
    echo "Create one: ezra hpc init-site $EZRA_SITE" >&2
    exit 1
  fi
  [[ -f "$SITE_DIR/ezra.yaml" ]] && export EZRA_CONFIG="${EZRA_CONFIG:-$SITE_DIR/ezra.yaml}"
  if [[ -f "$SITE_DIR/modules.sh" ]]; then
    # shellcheck disable=SC1090
    source "$SITE_DIR/modules.sh"
  fi
else
  echo "Tip: ezra hpc init-site <name> && export EZRA_SITE=<name>  (see sites/README.md)"
  # EDIT ME only for a one-off without a site profile:
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

echo "=== EZRA serve on $(hostname) ==="
echo "EZRA_SITE=${EZRA_SITE:-<none>}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>}"
ezra doctor
command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi || true

MODEL="${MODEL:?Set MODEL=<gallery-name> before sbatch (e.g. MODEL=qwen2.5-7b-instruct)}"
HOST="${EZRA_HOST:-0.0.0.0}"
PORT="${EZRA_PORT:-8000}"

echo "Serving model: $MODEL on ${HOST}:${PORT}"
ezra models info "$MODEL" || {
  echo "Model not installed. Download first, e.g.:"
  echo "  MODEL=$MODEL sbatch scripts/hpc_download_all.sh"
  exit 1
}

if ezra serve --help >/dev/null 2>&1; then
  exec ezra serve --model "$MODEL" --host "$HOST" --port "$PORT"
else
  echo "ezra serve is not available in this build yet."
  echo "GPU/CPU allocation succeeded - install an inference backend, then re-submit."
  echo "Holding allocation briefly so you can attach / debug (CTRL+C or scancel to stop)."
  sleep "${EZRA_HOLD_SECONDS:-300}"
fi
