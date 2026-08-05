# OrbitDesk Support Agent

This project is my submission for my Internship assignment.

The goal of this project is to build a local AI support agent that can answer questions about OrbitDesk (a fictional workspace product). The complete project runs locally after downloading the required models, so there is no need for OpenAI or any other paid API.

The project uses LangGraph to control the workflow, sentence-transformers for document retrieval, and TinyLlama for generating answers.

---

# Features

- Runs completely on local machine
- No API keys required
- Uses LangGraph for workflow
- Retrieves relevant knowledge from markdown documents
- Generates answers using TinyLlama
- Verifies the generated answer before returning it
- Retries once if verification fails
- Handles out-of-scope questions safely

---

# Workflow

```
User Question
      |
      v
   Triage
      |
      +----------------------+
      |                      |
      v                      v
 Retrieve Docs        Direct Response
      |                      |
      +----------+-----------+
                 |
                 v
          Generate Answer
                 |
                 v
             Verification
                 |
        +--------+--------+
        |                 |
        v                 v
    Final Answer      Retry Once
```

---

# Models Used

| Purpose | Model |
|---------|-------|
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| LLM | TinyLlama/TinyLlama-1.1B-Chat-v1.0 |

If TinyLlama is slow on your system, you can replace it with:

```
Qwen/Qwen2.5-0.5B-Instruct
```

by changing the model name in `orbitdesk_agent.py`.

---

# Requirements

Minimum:

- Python 3.10+
- 4 GB RAM
- Around 2 GB free storage

Recommended:

- 8 GB RAM
- Multi-core CPU

No GPU is required.

---

# Project Structure

```
orbitdesk-agent/
│
├── orbitdesk_agent.py
├── requirements.txt
├── README.md
│
├── knowledge_base/
│   ├── 01_product_overview.md
│   ├── ...
│
├── tests/
│   └── test_graph.py
│
├── graph_diagram.py
├── sample_outputs.json
└── resolved_cases.json
```

---

# Installation

## 1. Clone the repository

```bash
cd orbitdesk-agent
```

## 2. Create a virtual environment

Linux/macOS

```bash
python -m venv venv
source venv/bin/activate
```

Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

The first run downloads the required Hugging Face models, so it may take some time depending on your internet connection.

---

# Knowledge Base

Place all the provided markdown files inside the `knowledge_base` folder.

Example:

```
knowledge_base/
├── 01_product_overview.md
├── 02_roles_and_permissions.md
├── ...
└── 10_security_and_safe_responses.md
```

---

# Run the Project

```bash
python orbitdesk_agent.py
```

This will:

- Load all knowledge base files
- Load the embedding and language models
- Build the embedding index
- Run sample questions
- Save outputs to `sample_outputs.json`

---

# Running a Single Query

```python
from orbitdesk_agent import KnowledgeBase, ModelManager, build_agent, run_agent

kb = KnowledgeBase("knowledge_base")
kb.load_documents()

mm = ModelManager()
mm.load_models()

kb.build_index(mm.embedding_model)

agent = build_agent(kb, mm)

result = run_agent(
    "Can a Viewer create API credentials?",
    kb,
    agent
)

print(result["final_output"])
```

---

# Running Tests

```bash
python -m pytest tests/test_graph.py -v
```

or

```bash
python tests/test_graph.py
```

---

# Design Decisions

Some decisions I made while building this project:

- Used embedding-based routing instead of another classification model to keep the project lightweight.
- Added keyword-based checks before retrieval for faster routing.
- Added a verification step to reduce hallucinations.
- Limited retries to one attempt to avoid infinite loops.
- Designed everything to work well on a normal CPU without needing a GPU.

---

# Current Limitations

- TinyLlama is a small model, so answers may not always be perfect.
- Vector embeddings are stored in memory instead of using a vector database.
- The project processes one request at a time.

---

# Future Improvements

If I continue this project, I would like to add:

- Better reranking using a Cross Encoder
- Quantized GGUF models through llama.cpp
- Streaming responses
- Better structured JSON output
- A simple web interface using FastAPI or Streamlit
- FAISS or ChromaDB for larger knowledge bases

---

# What I Learned

While working on this project, I got hands-on experience with LangGraph, document retrieval using embeddings, local LLMs, and building a complete RAG pipeline. It also helped me understand how verification and retry logic can improve response quality.

Overall, this project gave me a good understanding of how AI support agents are built without relying on cloud APIs.
