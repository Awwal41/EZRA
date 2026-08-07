"""Best-effort local hardware probe (stdlib only)."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GpuInfo:
    name: str
    vram_total_mb: int

    @property
    def vram_gb(self) -> float:
        return self.vram_total_mb / 1024.0


@dataclass(frozen=True)
class SystemInfo:
    """Detected host resources for model fit checks."""

    ram_total_gb: float
    cpu_count: int
    gpus: tuple[GpuInfo, ...] = ()
    platform: str = field(default_factory=lambda: platform.system())

    @property
    def has_gpu(self) -> bool:
        return bool(self.gpus)

    @property
    def total_vram_gb(self) -> float:
        return sum(g.vram_gb for g in self.gpus)

    @property
    def effective_memory_gb(self) -> float:
        """Memory budget used for fit checks.

        Prefer aggregate GPU VRAM when present; otherwise ~80% of system RAM
        (leaves headroom for OS and runtime overhead on CPU/GGUF runs).
        """
        if self.has_gpu and self.total_vram_gb > 0:
            return self.total_vram_gb
        return max(0.0, self.ram_total_gb * 0.8)

    def summary_lines(self) -> list[str]:
        lines = [
            f"CPU cores:  {self.cpu_count}",
            f"System RAM: {self.ram_total_gb:.1f} GB",
        ]
        if self.gpus:
            for i, gpu in enumerate(self.gpus):
                lines.append(
                    f"GPU {i}:     {gpu.name} ({gpu.vram_gb:.1f} GB VRAM)"
                )
            lines.append(f"Fit budget: {self.effective_memory_gb:.1f} GB (GPU VRAM)")
        else:
            lines.append(
                f"GPU:       none detected (nvidia-smi)"
            )
            lines.append(
                f"Fit budget: {self.effective_memory_gb:.1f} GB (~80% of RAM)"
            )
        return lines


def _ram_total_gb() -> float:
    system = platform.system()
    if system == "Windows":
        return _ram_windows_gb()
    # Linux / macOS / most Unix
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        if pages > 0 and page_size > 0:
            return (pages * page_size) / (1024.0**3)
    except (AttributeError, OSError, ValueError):
        pass
    # macOS fallback via sysctl
    if system == "Darwin":
        try:
            out = subprocess.check_output(
                ["sysctl", "-n", "hw.memsize"],
                text=True,
                timeout=5,
                stderr=subprocess.DEVNULL,
            ).strip()
            return int(out) / (1024.0**3)
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    return 0.0


def _ram_windows_gb() -> float:
    try:
        import ctypes
        from ctypes import wintypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", wintypes.DWORD),
                ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return stat.ullTotalPhys / (1024.0**3)
    except (AttributeError, OSError, ValueError):
        pass
    return 0.0


def _probe_nvidia_gpus() -> tuple[GpuInfo, ...]:
    if not shutil.which("nvidia-smi"):
        return ()
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=10,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return ()

    gpus: list[GpuInfo] = []
    for line in out.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # "NVIDIA GeForce RTX 4090, 24564"
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 2:
            continue
        name = parts[0]
        try:
            vram_mb = int(float(parts[1]))
        except ValueError:
            continue
        gpus.append(GpuInfo(name=name, vram_total_mb=vram_mb))
    return tuple(gpus)


def probe_system() -> SystemInfo:
    """Detect RAM, CPU count, and NVIDIA GPUs on this host."""
    return SystemInfo(
        ram_total_gb=round(_ram_total_gb(), 2),
        cpu_count=os.cpu_count() or 1,
        gpus=_probe_nvidia_gpus(),
    )
