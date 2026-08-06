#!/usr/bin/env bash
#SBATCH --job-name=ezra-interactive
#SBATCH --output=ezra-interactive-%j.out
#SBATCH --error=ezra-interactive-%j.err
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
# ── EDIT ME (or use a site profile instead of editing this file) ──────────
# #SBATCH --partition=gpu
# #SBATCH --account=mylab
#
# Preferred: ezra hpc init-site my-cluster && export EZRA_SITE=my-cluster
# See sites/README.md

# EZRA SLURM job: hold a GPU node for interactive EZRA work.
# Usage:
#   export EZRA_SITE=my-cluster
#   sbatch scripts/hpc_interactive.sh
#   srun --jobid=<JOBID> --pty bash

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

MODEL="${MODEL:-}"
echo "=== EZRA interactive on $(hostname) ==="
echo "EZRA_SITE=${EZRA_SITE:-<none>}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-<unset>}"
ezra doctor
command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi || true

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
