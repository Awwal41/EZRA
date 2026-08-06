#!/usr/bin/env bash
#SBATCH --job-name=ezra-download
#SBATCH --output=ezra-download-%j.out
#SBATCH --error=ezra-download-%j.err
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
# Optional: request network / internet node partition if your site needs it
# #SBATCH --partition=download

# EZRA SLURM job: stage curated free models onto shared storage (CPU, no GPU).
# Usage:
#   sbatch scripts/hpc_download_all.sh
#   sbatch --export=ALL,EZRA_MODELS_DIR=/scratch/$USER/ezra/models scripts/hpc_download_all.sh
#   MODEL=qwen2.5-7b-instruct sbatch scripts/hpc_download_all.sh
#   ezra hpc submit download
#
# Prefer generating a site-tuned script:
#   ezra hpc script download --partition download -o /tmp/ezra-dl.sh

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

# Load your site's modules if needed, e.g.:
# module load python/3.11

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -U pip
pip install -q -e .

echo "=== EZRA download on $(hostname) ==="
ezra doctor

if [[ -n "${MODEL:-}" ]]; then
  echo "Downloading single model: $MODEL"
  ezra models download "$MODEL" --workers "${EZRA_WORKERS:-2}"
else
  echo "Downloading all free (non-gated) models under ${MAX_SIZE:-14}B..."
  ezra models download --all --no-gated --max-size "${MAX_SIZE:-14}" --workers "${EZRA_WORKERS:-2}"
fi

ezra models status
