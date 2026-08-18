# FranchiseOps RAG Builder

Standalone pipeline that builds the retrieval index powering the FranchiseOps AI copilot's grounded, document-based answers (SOPs, franchise agreements, FSSAI guidelines, and policy documents).

This folder is **not** the runtime app — it's the offline/preprocessing step. Run it once (or whenever source documents change) to produce the vector index that `FranchiseOps_AI_Final_Code/` loads at runtime.

---

## Table of Contents
1. [What This Does](#what-this-does)
2. [Pipeline Overview](#pipeline-overview)
3. [Folder Structure](#folder-structure)
4. [Setup & Usage](#setup--usage)
5. [Configuration](#configuration)
6. [Output](#output)
7. [Rebuilding the Index](#rebuilding-the-index)
8. [Notes & Limitations](#notes--limitations)

---

## What This Does

The main FranchiseOps AI copilot needs to answer questions grounded in real documents — SOPs, franchise agreements, compliance guidelines — instead of hallucinating. This builder takes raw source documents, chunks them, embeds them, and stores them in a ChromaDB vector store that the main app queries at inference time via LangChain's retrieval chain.

---

## Pipeline Overview

```
Raw Documents (PDF / DOCX / TXT)
            ▼
      Document Loader
            ▼
      Text Chunking          ← chunk size / overlap configured in `[FILL IN — config file/variable name]`
            ▼
   Embedding Generation      ← sentence-transformers model: `[FILL IN — exact model name, e.g. all-MiniLM-L6-v2]`
            ▼
   ChromaDB Vector Store     ← persisted to `[FILL IN — output path, e.g. ./chroma_db/]`
            ▼
  Consumed by llm_engine_franchise.py at runtime (FranchiseOps_AI_Final_Code)
```

---

## Folder Structure

```
FranchiseOps_RAG_Builder/
├── README.md
├── [FILL IN — e.g. build_index.py]      ← main entry point, runs the full pipeline
├── [FILL IN — e.g. loaders.py]          ← document loading / parsing
├── [FILL IN — e.g. chunker.py]          ← text splitting logic
├── [FILL IN — e.g. embedder.py]         ← embedding generation
├── docs/                                 ← source documents to index (SOPs, agreements, guidelines)
└── chroma_db/                            ← generated vector store output (gitignored)
```

---

## Setup & Usage

```bash
# 1. Navigate to this folder
cd FranchiseOps_RAG_Builder

# 2. Install dependencies (or reuse the main project's venv)
pip install -r requirements.txt

# 3. Place source documents to be indexed
# Drop PDFs / DOCX / TXT files into docs/

# 4. Run the builder
python [FILL IN — e.g. build_index.py]
```

On completion, a persisted ChromaDB store is written to the output directory, ready to be picked up by the main app's RAG layer.

---

## Configuration

| Setting | Purpose | Where it's set |
|---|---|---|
| Chunk size / overlap | Controls how documents are split before embedding | `[FILL IN]` |
| Embedding model | Converts text chunks into vectors | `[FILL IN — e.g. sentence-transformers/all-MiniLM-L6-v2]` |
| Vector store path | Where the ChromaDB index is persisted | `[FILL IN]` |
| Source documents path | Where raw input documents are read from | `docs/` |

No API keys or secrets are required for this step unless the embedding model is pulled from Hugging Face — in that case, `HF_TOKEN` is reused from the main project's `.env`.

---

## Output

- A persisted **ChromaDB** vector store (directory of embeddings + metadata)
- This output is consumed directly by `llm_engine_franchise.py` in `FranchiseOps_AI_Final_Code/` for retrieval-augmented answers, and by **Agent 9 (PDF SOP & Franchise Agreement RAG Studio)** for document-specific Q&A.

The generated vector store directory should be excluded from git (see `.gitignore`) — it's a build artifact, not source code. Only the source documents in `docs/` and the pipeline scripts need to be version-controlled.

---

## Rebuilding the Index

Re-run the builder any time source documents in `docs/` are added, removed, or updated:

```bash
python [FILL IN — e.g. build_index.py] --rebuild
```

`[FILL IN — note whether the script does a full rebuild each time, or supports incremental updates]`

---

## Notes & Limitations

- Indexing is a manual/offline step — there's no automatic re-index trigger when source documents change.
- Large documents may take noticeably longer to embed on CPU; a GPU runtime (e.g. Colab T4) speeds this up significantly.
- The quality of grounded answers in the main copilot depends directly on the documents placed in `docs/` — keep source documents current and relevant.
