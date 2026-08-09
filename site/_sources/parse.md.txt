# Document parsing

EZRA can turn papers, notes, and lab files into **LLM-ready text** via
`ezra.parse`. The Quivr [MegaParse](https://github.com/QuivrHQ/MegaParse)
library is vendored under [`third_party/MegaParse/`](../third_party/MegaParse/)
(Apache-2.0) and wrapped so the rest of EZRA never imports MegaParse directly.

## Install

```bash
# Lightweight: plain text + simple PDF extract
pip install -e ".[parse-basic]"

# Full MegaParse (PDF / Word / PowerPoint, tables, layout). Python ≥ 3.11
pip install -e ".[parse]"
# Also install system tools: poppler, tesseract (+ libmagic on macOS)
```

Check status: `ezra doctor` (look for **MegaParse**).

## Python API

```python
from ezra.parse import parse_file, DocumentParser

doc = parse_file("paper.pdf")          # backend=auto
print(doc.text)
print(doc.as_chat_context())           # ready for chat / agents

parser = DocumentParser(backend="megaparse", strategy="fast")
doc = parser.parse("slides.pptx")
```

| Backend | When to use |
|---------|-------------|
| `auto` (default) | Text → basic; rich Office/PDF → MegaParse if installed, else basic PDF |
| `basic` | Notes, SMILES, CIF, Markdown, simple digital PDFs (`pypdf`) |
| `megaparse` | Loss-minimizing PDF / DOCX / PPTX (requires `.[parse]`) |

## CLI

```bash
ezra parse notes.md
ezra parse paper.pdf -o paper.md
ezra parse deck.pptx --backend megaparse --strategy fast
ezra parse paper.pdf --json

# Attach a document to chat
ezra chat --file paper.pdf --model qwen2.5-7b-instruct -p "Summarize the methods"
```

## Config

In `ezra.yaml`:

```yaml
parse:
  backend: auto        # auto | basic | megaparse
  strategy: auto       # auto | fast | hi_res
```

## Layout / ONNX note

Hi-res MegaParse layout detection expects a DocLayNet ONNX model that is **not**
shipped in the EZRA git tree (large binary). Prefer `strategy: fast` unless you
install full upstream MegaParse weights. See
[`third_party/MegaParse/README.md`](../third_party/MegaParse/README.md).
