#!/usr/bin/env bash
# Site module / environment hook for EZRA SBATCH jobs.
#
# Sourced automatically when:  export EZRA_SITE=<this-folder-name>
#
# ── CUSTOMIZE (EDIT ME) ─────────────────────────────────────────────────────
# Uncomment and set the module / conda lines your cluster docs recommend.
# Do NOT put secrets here — use HF_TOKEN in the environment instead.
# ────────────────────────────────────────────────────────────────────────────

# module purge
# module load python/3.11
# module load cuda/12.4
# module load gcc/11

# Optional: conda / singularity / apptainer
# source /path/to/conda.sh && conda activate ezra

# Optional: confirm the python that will run EZRA
# which python3
