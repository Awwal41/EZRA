#!/usr/bin/env bash
#SBATCH --job-name=ezra-serve
#SBATCH --output=ezra-serve-%j.out
#SBATCH --error=ezra-serve-%j.err
#SBATCH --time=08:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
# Optional site knobs (uncomment / edit):
# #SBATCH --partition=gpu
# #SBATCH --account=myaccount
# #SBATCH --constraint=a100

# EZRA SLURM job: serve a model with GPU/CPU allocation.
# Usage:
#   MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_serve_gpu.sh
#   ezra hpc submit serve --model qwen2.5-7b-instruct --gpus 1
#
# Prefer generating a site-tuned script:
#   ezra hpc script serve --model qwen2.5-7b-instruct --partition gpu -o /tmp/ezra-serve.sh

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

# module load python/3.11
# module load cuda/12.4

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -U pip
pip install -q -e .

echo "=== EZRA serve on $(hostname) ==="
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
  echo "GPU/CPU allocation succeeded — install an inference backend, then re-submit."
  echo "Holding allocation briefly so you can attach / debug (CTRL+C or scancel to stop)."
  sleep "${EZRA_HOLD_SECONDS:-300}"
fi
