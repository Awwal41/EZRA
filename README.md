# EZRA
EZRA: Easy Zero-setup Routing Assistant for local &amp; HPC LLMs A researcher-first system for downloading, running, and intelligently routing free/open LLMs locally or on HPC, purpose-built for people building and applying LLMs in materials science and chemistry.

Core Vision
Most local LLM tools (Ollama, LM Studio, LocalAI, etc.) are general-purpose. Most routers are either pure cloud cost-optimizers or heavy production gateways.
EZRA sits in the sweet spot for scientific developers:

One-click download & local run of free open models
Smart router that seamlessly switches between multiple local models and remote HPC endpoints
Domain-aware defaults, prompts, tools, and evaluation hooks for materials science & chemistry workflows
Privacy-first (data stays local or on your institutional HPC)
Designed so a grad student or postdoc can go from “I have a laptop” to “I am iterating on chemistry-specialized agents” in under an hour

Key Features
1. Free LLM Download & Local Runtime

Curated gallery of high-quality free/open models with chemistry/materials relevance (e.g., Qwen, Llama, Mistral, DeepSeek, Gemma variants, and science-tuned checkpoints when available)
One-command or GUI download from Hugging Face / official sources with automatic quantization selection (GGUF, AWQ, GPTQ, MLX, etc.)
Runs on consumer hardware (CPU, NVIDIA, AMD, Apple Silicon) via backends such as llama.cpp, vLLM, MLX, and others
Automatic VRAM / RAM management, model hot-swapping, and keep-alive policies
OpenAI-compatible local API so existing tools (LangChain, LlamaIndex, Cursor, Open WebUI, custom agents) work with almost no change

2. Intelligent Multi-Model Router

Local ↔ Local switching: route simple queries to small/fast models, complex reasoning or long-context chemistry tasks to larger ones
Local ↔ HPC seamless failover or intentional routing: send heavy jobs (long context, large models, batch inference, agent loops) to institutional HPC while keeping interactive work local
Complexity / domain classifiers (token count, code presence, chemical terminology, SMILES/CIF detection, reasoning markers, etc.)
Manual override + “auto” mode + session pinning
Policy engine: prefer local for privacy, prefer HPC for speed/quality, cost/latency SLOs, model capability matching
Fallback chains and health checks so a failed local model or offline HPC does not break the workflow

3. Materials Science & Chemistry Specialization

Built-in prompt templates and system prompts for common tasks: property prediction, synthesis planning, literature extraction, structure reasoning, SMILES/SELFIES handling, CIF interpretation, etc.
Tool-calling / function-calling support for scientific tools (Materials Project, PubChem, RDKit-style chemistry ops, ASE / pymatgen style structure handling, simulation launchers)
Easy integration points for domain RAG (papers, internal notes, computational results)
Lightweight evaluation harness focused on chemistry/materials benchmarks so researchers can measure whether a new model or fine-tune actually helps their use case
Support for multimodal inputs later (structures, spectra, images of experimental setups)

4. Developer & Researcher Experience

Clean desktop / web UI + powerful CLI
Model browser with filters for size, license, science relevance, quantization, and hardware fit
Experiment tracking lite: save prompts, responses, which model was used, latency, and notes
Exportable configs so a whole lab can share the same model + router setup
Plugin / extension system for custom routers, tools, and backends
Logging and observability that respects research privacy (local by default)

5. HPC Bridge

Simple configuration for common HPC environments (SLURM, Globus Compute style, institutional inference services)
Secure, low-friction remote endpoints (OpenAI-compatible where possible)
Automatic detection of available remote models and resources
Streaming support so interactive use still feels responsive even when the heavy model lives on the cluster
Resource-aware routing (queue time, GPU availability, current load)
