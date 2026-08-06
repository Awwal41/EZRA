#!/usr/bin/env bash
# Site module / environment hook for EZRA SBATCH jobs.
#
# EDIT ME: uncomment and set the module (or conda) commands your cluster needs.
# This file is sourced automatically when EZRA_SITE=<this-folder-name> is set.
#
# Do NOT put secrets here. Use HF_TOKEN in the environment / job export instead.

# module purge
# module load python/3.11
# module load cuda/12.4
# module load gcc/11

# Optional: conda / singularity / apptainer activation
# source /path/to/conda.sh && conda activate ezra

# Optional: make sure pip/venv python is the one you expect
# which python3
