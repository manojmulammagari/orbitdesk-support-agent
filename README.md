# OrbitDesk Support Agent - Local AI Agent Network

> **AI Engineer Internship Assignment** | Tantrabodh AI  
> Built with LangGraph + Local Hugging Face Models (No API keys needed)

---

## What This Project Does

This is a **local-first AI support agent** that answers questions about **OrbitDesk** (a fictional workspace product) using:
- **LangGraph** for graph-based orchestration
- **sentence-transformers** for document retrieval
- **TinyLlama** (local LLM) for response generation
- **Verification + Retry logic** for quality control

The agent classifies questions, retrieves relevant docs, generates answers, verifies them, and retries if needed — all **offline** after initial model download.

---

## Architecture

```
User Question
    ↓
┌─────────────┐
│   TRIAGE    │  ← Embedding-based classification
└──────┬──────┘
       │
   ┌───┴───┐
   ▼       ▼
┌──────┐ ┌──────────┐
│Retrieve│ │Generate │  ← Clarification / Out-of-scope
│(KB docs)│ │(direct) │     skip retrieval
└───┬───┘ └────┬─────┘
    │          │
    └────┬─────┘
         ▼
    ┌─────────┐
    │ GENERATE│  ← Local LLM generates answer from context
    └────┬────┘
         ▼
    ┌─────────┐
    │ VERIFY  │  ← Checks sources, grounding, hallucinations
    └────┬────┘
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌────────┐
│ FINALIZE│  │ REVISE │  ← Retry once if failed
└────┬───┘  └───┬────┘
     │          │
     └────┬─────┘
          ▼
      ┌───────┐
      │  END  │
      └───────┘
```

---

## Models Used

| Purpose | Model | Size | Source |
|---------|-------|------|--------|
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | ~80MB | Hugging Face |
| Generation | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | ~600MB | Hugging Face |

**Alternative LLM:** If TinyLlama quality is poor on your hardware, swap to `Qwen/Qwen2.5-0.5B-Instruct` (~1GB) by editing `LLM_MODEL` in `orbitdesk_agent.py`.

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Any modern x86_64 | 4+ cores |
| RAM | 4GB | 8GB+ |
| Storage | 2GB free | 3GB free |
| GPU | Not required | Optional (speeds up LLM) |
| OS | Linux/macOS/Windows | Any |

**Tested on:** CPU-only laptop with 8GB RAM.

---

## Setup Instructions

### 1. Clone / Download This Repository

```bash
cd orbitdesk-agent
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Linux/macOS
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** First run will download ~700MB of models from Hugging Face. This is normal and happens only once.

### 4. Place Knowledge Base Files

Put all the provided `.md` knowledge base files into the `knowledge_base/` folder:

```
knowledge_base/
├── 01_product_overview.md
├── 02_roles_and_permissions.md
├── 03_workspace_settings_and_timezones.md
├── 04_scheduled_exports.md
├── 05_api_credentials.md
├── 06_connections_and_refreshes.md
├── 07_delivery_destinations.md
├── 08_escalation_and_diagnostics.md
├── 09_audit_logs.md
└── 10_security_and_safe_responses.md
```

### 5. Run the Agent

```bash
python orbitdesk_agent.py
```

This will:
1. Load all knowledge base documents
2. Download & load models (first time only)
3. Build the embedding index
4. Run 5 test questions through the graph
5. Print execution traces and final JSON outputs
6. Save results to `sample_outputs.json`

---

## Running Individual Questions

You can also run a single question:

```python
from orbitdesk_agent import KnowledgeBase, ModelManager, build_agent, run_agent

kb = KnowledgeBase("knowledge_base")
kb.load_documents()

mm = ModelManager()
mm.load_models()

kb.build_index(mm.embedding_model)
agent = build_agent(kb, mm)

result = run_agent("Can a Viewer create API credentials?", kb, agent)
print(result["final_output"])
```

---

## Running Tests

```bash
python -m pytest tests/test_graph.py -v
```

Or run directly:

```bash
python tests/test_graph.py
```

---

## Project Structure

```
orbitdesk-agent/
├── orbitdesk_agent.py          # Main agent (graph + nodes + models)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── knowledge_base/             # Place all .md KB files here
│   ├── 01_product_overview.md
│   └── ...
├── tests/
│   └── test_graph.py           # Automated routing tests
├── graph_diagram.py            # Generates architecture PNG
├── sample_outputs.json         # Generated after running
└── resolved_cases.json         # Auto-created if missing
```

---

## Key Design Decisions

1. **Embedding-based Triage:** Instead of a separate classification model, we reuse the embedding model with labeled examples. This reduces model count and load time.

2. **Keyword Guardrails:** Deterministic keyword checks catch obvious out-of-scope/escalation requests before the embedding classifier runs. Fast and reliable.

3. **Retry Loop with Cap:** Verification failures trigger exactly 1 retry (`retry_count < 1`), then fall back to safe escalation. Prevents infinite loops.

4. **CPU-First Design:** TinyLlama is chosen specifically for CPU inference. On 8GB RAM laptop, generation takes ~5-10 seconds per answer.

---

## Known Limitations

- **LLM Quality:** TinyLlama is small. Answers may occasionally be repetitive or miss nuance. This is expected — the assignment values orchestration over prose quality.
- **No Persistent Vector DB:** Uses in-memory numpy arrays. Fast for small KBs, but would need FAISS/Chroma for thousands of documents.
- **Single-Threaded:** No batching or async. Sufficient for demo purposes.

## What I Would Improve With More Time

1. Add a **reranker model** (like `cross-encoder/ms-marco-MiniLM-L-6-v2`) to improve retrieval precision.
2. Use **quantized LLM** (GGUF format via llama.cpp) for 2-3x faster CPU inference.
3. Add **structured output parsing** (JSON mode) to guarantee schema compliance.
4. Implement **streaming** for real-time response generation.

---

## License

This is a demonstration project for an internship assignment. Not for production use.
