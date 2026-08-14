# Which requirements file should I use?

Start from the EZRA folder with your virtual environment ON, then:

```bash
pip install -r <the file that matches your computer>
```

| File | Use when |
|------|----------|
| `requirements-ide-cpu.txt` | Windows or Linux, no NVIDIA GPU (most laptops) |
| `requirements-ide-cuda124.txt` | NVIDIA GPU, `nvidia-smi` shows CUDA 12.4, 12.5, or 12.6 |
| `requirements-ide-cuda121.txt` | NVIDIA GPU, `nvidia-smi` shows CUDA 12.1 |
| `requirements-ide-macos.txt` | Apple Silicon Mac (M1–M4), Metal wheel |
| `requirements.txt` | Core libraries only (no chat engine) |
| `requirements-serve.txt` | FastAPI only; still need a llama.cpp wheel |

A **wheel** is a pre-built `llama-cpp-python` package. The `requirements-ide-*.txt` files tell pip to use that wheel and **not** compile C++ on your machine.

Full walkthrough (no coding experience assumed): [docs/getting-started.md](../docs/getting-started.md)

If pip sits on `Building wheel for llama-cpp-python` for more than a minute, stop it (Ctrl+C) and use `requirements-ide-cpu.txt` instead of a plain `pip install llama-cpp-python`.
