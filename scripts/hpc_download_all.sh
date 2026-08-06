#!/usr/bin/env bash
#SBATCH --job-name=ezra-download
#SBATCH --output=ezra-download-%j.out
#SBATCH --error=ezra-download-%j.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
# ── EDIT ME (or use a site profile instead of editing this file) ──────────
# #SBATCH --partition=download
# #SBATCH --account=mylab
#
# Preferred workflow (customize once, commit & push for your cluster):
#   ezra hpc init-site my-cluster
#   $EDITOR sites/my-cluster/ezra.yaml    # partition, account, resources
#   $EDITOR sites/my-cluster/modules.sh   # module load …
#   export EZRA_SITE=my-cluster
#   ezra hpc submit download
# See sites/README.md

# EZRA SLURM job: stage curated free models onto shared storage (CPU, no GPU).
# Usage:
#   export EZRA_SITE=my-cluster   # optional but recommended
#   sbatch scripts/hpc_download_all.sh
#   MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_download_all.sh

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
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -U pip
pip install -q -e .

echo "=== EZRA download on $(hostname) ==="
echo "EZRA_SITE=${EZRA_SITE:-<none>}"
ezra doctor

if [[ -n "${MODEL:-}" ]]; then
  echo "Downloading single model: $MODEL"
  ezra models download "$MODEL" --workers "${EZRA_WORKERS:-2}"
else
  echo "Downloading all free (non-gated) models under ${MAX_SIZE:-14}B..."
  ezra models download --all --no-gated --max-size "${MAX_SIZE:-14}" --workers "${EZRA_WORKERS:-2}"
fi

ezra models status
