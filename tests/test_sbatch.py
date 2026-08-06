"""Tests for SBATCH script generation (no SLURM required)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ezra.hpc.sbatch import (
    JOB_KINDS,
    SlurmResources,
    generate_script,
    render_sbatch_header,
    resources_from_config,
    submit_script,
    write_script,
)


def test_header_requests_gpu_and_cpus() -> None:
    res = SlurmResources(
        job_name="ezra-serve",
        time="08:00:00",
        cpus=8,
        mem="64G",
        gpus=1,
        partition="gpu",
        account="mylab",
    )
    header = render_sbatch_header(res)
    assert "#SBATCH --gres=gpu:1" in header
    assert "#SBATCH --cpus-per-task=8" in header
    assert "#SBATCH --mem=64G" in header
    assert "#SBATCH --time=08:00:00" in header
    assert "#SBATCH --partition=gpu" in header
    assert "#SBATCH --account=mylab" in header


def test_gres_override_wins() -> None:
    res = resources_from_config(
        "serve",
        {"hpc": {"slurm": {"serve": {"gpus": 2, "gres": "gpu:a100:1"}}}},
    )
    header = render_sbatch_header(res)
    assert "#SBATCH --gres=gpu:a100:1" in header
    assert "#SBATCH --gres=gpu:2" not in header


def test_script_embeds_custom_models_dir() -> None:
    script = generate_script("download", models_dir="/data/ezra/models")
    assert "EZRA_MODELS_DIR=" in script
    assert "/data/ezra/models" in script
    assert "${SCRATCH:-$HOME}/ezra/models" not in script


def test_script_default_models_dir_uses_scratch_fallback() -> None:
    script = generate_script("download")
    assert "${SCRATCH:-$HOME}/ezra/models" in script


def test_download_has_no_gpu() -> None:
    script = generate_script("download")
    assert "#SBATCH --gres" not in script
    assert "ezra models download" in script


def test_serve_script_has_gpu_and_model_guard() -> None:
    script = generate_script("serve")
    assert "#SBATCH --gres=gpu:1" in script
    assert "ezra serve" in script
    assert "MODEL=" in script


def test_interactive_script() -> None:
    script = generate_script("interactive")
    assert "#SBATCH --gres=gpu:1" in script
    assert "EZRA_HOLD_SECONDS" in script


def test_all_kinds_are_bash_scripts() -> None:
    for kind in JOB_KINDS:
        script = generate_script(kind)
        assert script.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in script


def test_write_script(tmp_path: Path) -> None:
    path = write_script(tmp_path / "job.sh", generate_script("download"))
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")


def test_config_overrides_defaults() -> None:
    raw = {
        "hpc": {
            "slurm": {
                "partition": "gpu-shared",
                "serve": {"cpus": 16, "mem": "128G", "gpus": 2, "time": "12:00:00"},
            }
        }
    }
    res = resources_from_config("serve", raw)
    assert res.partition == "gpu-shared"
    assert res.cpus == 16
    assert res.mem == "128G"
    assert res.gpus == 2
    assert res.time == "12:00:00"
    assert res.gres == "gpu:2"


def test_with_overrides() -> None:
    res = resources_from_config("download").with_overrides(cpus=12, gpus=0, mem="16G")
    assert res.cpus == 12
    assert res.mem == "16G"


def test_submit_dry_run() -> None:
    cmd = submit_script(generate_script("download"), dry_run=True)
    assert "sbatch" in cmd
    assert "--export=" in cmd


def test_submit_without_sbatch_raises() -> None:
    with pytest.raises(FileNotFoundError, match="sbatch"):
        submit_script("#!/bin/bash\necho hi\n", dry_run=False)
