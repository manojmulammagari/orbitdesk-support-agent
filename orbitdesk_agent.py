"""
OrbitDesk Support Agent - Local-First AI Agent Network
Built with LangGraph + Local Hugging Face Models
"""

import os
import json
import re
import glob
import operator
from typing import TypedDict, List, Dict, Annotated, Literal
import numpy as np
from langgraph.graph import StateGraph, END
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# =============================================================================
# CONFIGURATION - Edit these if you want different models
# =============================================================================
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # ~80MB, very fast
LLM_MODEL = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"            # ~600MB, CPU-friendly
# ALTERNATIVE LLM (uncomment if TinyLlama gives poor results):
# LLM_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"                   # ~1GB, slightly better
DEVICE = "cuda"  # Change to "cuda" if you have a GPU

# =============================================================================
# STATE DEFINITION
# This is the shared state that passes between all nodes in the graph
# =============================================================================
class AgentState(TypedDict):
    question: str                           # The user's question
    classification: str                     # triage result: answerable/clarification/escalation/out_of_scope
    retrieved_docs: List[Dict]            # Documents found by retrieval
    generated_answer: str                 # Raw answer from LLM
    verification_result: Dict             # Did verification pass?
    final_output: Dict                    # Final structured JSON output
    retry_count: int                      # How many retries so far (loop protection)
    logs: Annotated[List[str], operator.add]  # Execution trace (auto-merged across nodes)

# =============================================================================
# KNOWLEDGE BASE
# Loads all .md files and resolved cases, chunks them, builds embeddings
# =============================================================================
class KnowledgeBase:
    def __init__(self, kb_dir="knowledge_base"):
        self.kb_dir = kb_dir
        self.documents = []      # Full documents
        self.chunks = []         # Searchable chunks
        self.embeddings = None   # Numpy array of embeddings
        self.embedding_model = None

    def load_documents(self):
        """Load all markdown files from the knowledge_base folder."""
        md_files = sorted(glob.glob(os.path.join(self.kb_dir, "*.md")))
        if not md_files:
            raise FileNotFoundError(f"No .md files found in {self.kb_dir}. Please place the KB files there.")

        for filepath in md_files:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata from YAML frontmatter
            doc_id = None
            title = None
            lines = content.split('\n')
            for line in lines[:25]:
                if line.startswith('document_id:'):
                    doc_id = line.split(':', 1)[1].strip()
                elif line.startswith('title:'):
                    title = line.split(':', 1)[1].strip()

            filename = os.path.basename(filepath)
            if not doc_id:
                doc_id = filename.replace('.md', '')
            if not title:
                title = doc_id

            self.documents.append({
                "id": doc_id,
                "title": title,
                "filename": filename,
                "content": content
            })

            # Split document into chunks by headers for better retrieval
            chunks = self._split_into_chunks(content, doc_id, title, filename)
            self.chunks.extend(chunks)

        # Load resolved cases
        self._load_resolved_cases()

        print(f"[KB] Loaded {len(self.documents)} documents, {len(self.chunks)} chunks")

    def _split_into_chunks(self, content, doc_id, title, filename):
        """Split a document into chunks using markdown headers."""
        chunks = []
        # Split on ## or ### headers
        sections = re.split(r'\n##+\s+', content)

        for i, section in enumerate(sections):
            if not section.strip():
                continue
            lines = section.split('\n')
            header = lines[0].strip() if lines else ""
            body = '\n'.join(lines[1:]).strip()

            chunk_text = f"{header}\n{body}" if body else header
            if len(chunk_text) < 30:  # Skip tiny fragments
                continue

            chunks.append({
                "doc_id": doc_id,
                "doc_title": title,
                "filename": filename,
                "header": header,
                "content": chunk_text[:800],  # Limit chunk size
                "chunk_id": f"{doc_id}_chunk_{i}"
            })
        return chunks

    def _load_resolved_cases(self):
        """Load resolved_cases.json or create it if missing."""
        cases_file = "resolved_cases.json"
        if os.path.exists(cases_file):
            with open(cases_file, 'r') as f:
                cases = json.load(f)
        else:
            # Create mock resolved cases based on the knowledge base
            cases = [
                {
                    "case_id": "CASE-001",
                    "question": "Scheduled exports stopped after timezone change",
                    "resolution": "Resave the schedule after timezone change per KB-003. Open schedule, review next-run time, click Save schedule. Also check KB-004 for missed export troubleshooting.",
                    "status": "resolved",
                    "superseded": False,
                    "source_docs": ["KB-003", "KB-004"]
                },
                {
                    "case_id": "CASE-002",
                    "question": "Viewer cannot create API credentials",
                    "resolution": "Viewers do not have permission to create API credentials. Only Owners and Admins can create credentials per KB-002 and KB-005.",
                    "status": "resolved",
                    "superseded": False,
                    "source_docs": ["KB-002", "KB-005"]
                },
                {
                    "case_id": "CASE-003",
                    "question": "Connection keeps showing reauthorization_required",
                    "resolution": "Owner or Admin must reconnect the data source. If repeated connector_internal_error occurs, escalate after two failed attempts with connection ID and timestamps per KB-008.",
                    "status": "resolved",
                    "superseded": False,
                    "source_docs": ["KB-006", "KB-008"]
                },
                {
                    "case_id": "CASE-004",
                    "question": "Legacy personal API tokens not working",
                    "resolution": "Legacy personal API tokens were removed in OrbitDesk 4.0. Use workspace credentials created by Owner or Admin instead. KB-005.",
                    "status": "resolved",
                    "superseded": True,
                    "source_docs": ["KB-005"]
                }
            ]
            with open(cases_file, 'w') as f:
                json.dump(cases, f, indent=2)

        for case in cases:
            self.chunks.append({
                "doc_id": case["case_id"],
                "doc_title": f"Resolved Case {case['case_id']}",
                "filename": "resolved_cases.json",
                "header": case["question"],
                "content": f"Case {case['case_id']}: {case['question']}\nResolution: {case['resolution']}\nStatus: {case['status']}\nSuperseded: {case.get('superseded', False)}",
                "chunk_id": case["case_id"],
                "is_case": True,
                "superseded": case.get("superseded", False)
            })

    def build_index(self, embedding_model):
        """Build the embedding index for fast similarity search."""
        self.embedding_model = embedding_model
        texts = [c["content"] for c in self.chunks]
        print(f"[KB] Building embeddings for {len(texts)} chunks... (this may take a minute)")
        self.embeddings = embedding_model.encode(texts, show_progress_bar=True)
        print("[KB] Index built successfully!")

    def search(self, query, top_k=5):
        """Search for the most relevant chunks given a query."""
        query_embedding = self.embedding_model.encode([query])
        similarities = np.dot(self.embeddings, query_embedding.T).flatten()
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk["score"] = float(similarities[idx])
            results.append(chunk)
        return results

# =============================================================================
# MODEL MANAGER
# Loads the local embedding model and LLM
# =============================================================================
class ModelManager:
    def __init__(self):
        self.embedding_model = None
        self.tokenizer = None
        self.llm = None
        self.llm_pipeline = None

    def load_models(self):
        print(f"[MODELS] Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)
        print("[MODELS] Embedding model loaded ✓")

        print(f"[MODELS] Loading LLM: {LLM_MODEL}")
        print("[MODELS] This may take a few minutes on first run (downloading ~600MB)...")
        self.tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)

        # Load model with appropriate settings for CPU
        load_kwargs = {"torch_dtype": "auto"}
        if DEVICE == "cpu":
            load_kwargs["low_cpu_mem_usage"] = True
        else:
            load_kwargs["device_map"] = "auto"

        self.llm = AutoModelForCausalLM.from_pretrained(LLM_MODEL, **load_kwargs)

        self.llm_pipeline = pipeline(
            "text-generation",
            model=self.llm,
            tokenizer=self.tokenizer,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
            device=0 if DEVICE == "cuda" else -1
        )
        print("[MODELS] LLM loaded successfully ✓")

# =============================================================================
# TRIAGE CLASSIFIER
# Uses embeddings to classify questions into 4 categories
# =============================================================================
class TriageClassifier:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

        # Labeled examples for few-shot embedding classification
        self.examples = [
            # Answerable examples
            ("Can a Viewer create API credentials?", "answerable"),
            ("How do I change the workspace timezone?", "answerable"),
            ("What should I check if scheduled exports stop working?", "answerable"),
            ("How long are audit logs retained?", "answerable"),
            ("Who can create connections in OrbitDesk?", "answerable"),

            # Clarification examples
            ("It's not working", "clarification"),
            ("Help me with exports", "clarification"),
            ("Sync is not working", "clarification"),
            ("I have a problem", "clarification"),
            ("Something broke", "clarification"),

            # Escalation examples
            ("I need to escalate this issue", "escalation"),
            ("Two consecutive render_failed events for same dashboard", "escalation"),
            ("Suspected credential exposure", "escalation"),
            ("Billing dispute", "escalation"),
            ("Human support needed", "escalation"),

            # Out of scope examples
            ("Write a refund for my subscription", "out_of_scope"),
            ("What is the weather today?", "out_of_scope"),
            ("Help me with my taxes", "out_of_scope"),
            ("Legal advice needed", "out_of_scope"),
            ("Medical question", "out_of_scope"),
        ]
        self.example_embeddings = embedding_model.encode([ex[0] for ex in self.examples])
        self.example_labels = [ex[1] for ex in self.examples]

    def classify(self, question):
        """Classify a question using keyword guards + embedding similarity."""
        q_lower = question.lower()

        # --- DETERMINISTIC GUARDRAILS (fast, reliable) ---
        out_of_scope_keywords = ["refund", "subscription", "legal advice", "weather", 
                                  "tax", "medical", "unrelated", "not orbitdesk", "cancel subscription"]
        if any(kw in q_lower for kw in out_of_scope_keywords):
            return "out_of_scope", 0.95

        escalation_keywords = ["escalate", "human support", "billing", "ownership dispute", 
                                "credential exposure", "suspected exposure", "legal request"]
        if any(kw in q_lower for kw in escalation_keywords):
            return "escalation", 0.9

        # Very short + vague = clarification
        if len(question.split()) < 6:
            vague_words = ["not working", "broken", "issue", "problem", "help", "error"]
            if any(vw in q_lower for vw in vague_words):
                return "clarification", 0.85

        # --- EMBEDDING-BASED CLASSIFICATION ---
        q_embedding = self.embedding_model.encode([question])
        similarities = np.dot(self.example_embeddings, q_embedding.T).flatten()
        top_idx = np.argmax(similarities)
        top_sim = similarities[top_idx]
        label = self.example_labels[top_idx]

        # If similarity is too low, default to clarification (safe fallback)
        if top_sim < 0.45:
            return "clarification", float(top_sim)

        return label, float(top_sim)

# =============================================================================
# RESPONSE GENERATOR
# Uses the local LLM to generate answers from retrieved context
# =============================================================================
class ResponseGenerator:
    def __init__(self, model_manager):
        self.model_manager = model_manager

    def generate(self, question, retrieved_docs, classification, retry_count=0):
        """Generate an answer using only the retrieved evidence."""
        # Build context string from top documents
        context_parts = []
        for i, doc in enumerate(retrieved_docs[:3]):
            source_tag = f"[{doc['doc_id']}]"
            context_parts.append(f"Source {i+1} {source_tag}:{doc['content'][:600]}")
        context = "".join(context_parts)

        # Build the prompt based on classification
        if classification == "answerable":
            system_msg = "You are the OrbitDesk Support Agent. Answer using ONLY the provided sources."
            rules = [
                "- Include source references like [KB-XXX] or [CASE-XXX] in your answer",
                "- Be concise and accurate",
                "- Do not invent information not in the sources",
                "- Do not claim to perform actions (refunds, account changes, etc.)"
            ]
        elif classification == "escalation":
            system_msg = "You are the OrbitDesk Support Agent. The user needs human support."
            rules = [
                "- Explain what diagnostic info to collect before escalating",
                "- Reference the relevant knowledge base documents",
                "- Do not promise resolution times"
            ]
        else:
            system_msg = "You are the OrbitDesk Support Agent."
            rules = ["- Answer based only on the provided sources"]

        # Add retry instruction if this is a retry attempt
        retry_note = ""
        if retry_count > 0:
            retry_note = "IMPORTANT: This is a retry. Ensure you include specific source references like [KB-XXX] and stay strictly within the provided documentation."

        rules_text = "".join(rules)

        prompt = f"""{system_msg}{retry_note}

Rules:
{rules_text}

Sources:
{context}

Question: {question}

Answer:"""

        # Generate with the local LLM
        result = self.model_manager.llm_pipeline(
            prompt,
            max_new_tokens=200,
            do_sample=True,
            temperature=0.3,
            return_full_text=False
        )
        answer = result[0]["generated_text"].strip()

        # Clean up - truncate if the model starts generating a new prompt
        for marker in ["Sources:", "Question:", "User:", "Assistant:", "Answer:"]:
            if f"{marker}" in answer:
                answer = answer.split(f"{marker}")[0].strip()

        return answer

# =============================================================================
# VERIFIER
# Checks if the generated answer meets quality criteria
# =============================================================================
class Verifier:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model

    def verify(self, question, answer, retrieved_docs, classification):
        """Verify the answer against quality rules."""
        issues = []

        # Rule 1: Answerable questions must have source references
        if classification == "answerable":
            source_pattern = r'\[([A-Z]+-\d+)\]'
            sources_found = re.findall(source_pattern, answer)
            if not sources_found:
                issues.append("No source references like [KB-XXX] found in answer")
        else:
            sources_found = []

        # Rule 2: Answer must be grounded in retrieved docs (embedding similarity)
        if retrieved_docs and answer:
            answer_emb = self.embedding_model.encode([answer])
            doc_embs = [self.embedding_model.encode([d["content"]]) for d in retrieved_docs[:3]]
            sims = [np.dot(answer_emb, de.T).flatten()[0] for de in doc_embs]
            max_sim = max(sims) if sims else 0
            if max_sim < 0.25:
                issues.append("Answer appears poorly grounded in retrieved evidence")
        else:
            max_sim = 0

        # Rule 3: Answer must be non-empty and meaningful
        if len(answer) < 25:
            issues.append("Answer too short or empty")

        # Rule 4: No hallucinated action claims
        forbidden = ["i have processed", "i have completed", "i will contact", 
                     "i have issued", "i have refunded", "i have changed"]
        for phrase in forbidden:
            if phrase in answer.lower():
                issues.append(f"Contains unsupported action claim: '{phrase}'")

        passed = len(issues) == 0
        return {
            "passed": passed,
            "issues": issues,
            "sources_found": sources_found,
            "grounding_score": float(max_sim)
        }

# =============================================================================
# GRAPH NODES
# Each function below is a node in the LangGraph workflow
# =============================================================================

def triage_node(state: AgentState, classifier: TriageClassifier) -> AgentState:
    """Classify the incoming question."""
    question = state["question"]
    classification, confidence = classifier.classify(question)

    return {
        **state,
        "classification": classification,
        "logs": [f"TRIAGE: question classified as '{classification}' (confidence: {confidence:.2f})"]
    }

def retrieve_node(state: AgentState, kb: KnowledgeBase) -> AgentState:
    """Retrieve relevant documents from the knowledge base."""
    # Skip retrieval for clarification and out_of_scope
    if state["classification"] in ["clarification", "out_of_scope"]:
        return {
            **state,
            "retrieved_docs": [],
            "logs": ["RETRIEVE: skipped (classification is clarification/out_of_scope)"]
        }

    docs = kb.search(state["question"], top_k=5)
    logs = [f"RETRIEVE: found {len(docs)} relevant chunks"]
    for d in docs[:3]:
        logs.append(f"  → {d['chunk_id']} (score: {d['score']:.3f})")

    return {**state, "retrieved_docs": docs, "logs": logs}

def generate_node(state: AgentState, generator: ResponseGenerator) -> AgentState:
    """Generate a response based on classification and retrieved docs."""
    classification = state["classification"]

    if classification == "clarification":
        answer = (
            "I need more information to help you effectively. Could you please provide:"
            "1. The specific feature or object affected (dashboard, connection, schedule, etc.)"
            "2. Any error codes or messages you're seeing"
            "3. What you were trying to do when the issue occurred"
            "4. Your workspace role (Owner, Admin, Analyst, or Viewer)"
        )
    elif classification == "out_of_scope":
        answer = (
            "This request is outside the scope of OrbitDesk support. "
            "I can only assist with questions about OrbitDesk features, troubleshooting, and usage. "
            "For billing, refunds, or legal matters, please contact the appropriate team directly."
        )
    else:
        # answerable or escalation - use the LLM
        answer = generator.generate(
            state["question"],
            state["retrieved_docs"],
            classification,
            retry_count=state.get("retry_count", 0)
        )

    return {
        **state,
        "generated_answer": answer,
        "logs": [f"GENERATE: produced answer ({len(answer)} chars) for '{classification}'"]
    }

def verify_node(state: AgentState, verifier: Verifier) -> AgentState:
    """Verify the generated answer meets quality standards."""
    # Skip verification for clarification and out_of_scope
    if state["classification"] in ["clarification", "out_of_scope"]:
        return {
            **state,
            "verification_result": {"passed": True, "issues": [], "sources_found": [], "grounding_score": 1.0},
            "logs": ["VERIFY: skipped for clarification/out_of_scope"]
        }

    result = verifier.verify(
        state["question"],
        state["generated_answer"],
        state["retrieved_docs"],
        state["classification"]
    )

    status = "PASSED" if result["passed"] else "FAILED"
    issue_str = ", ".join(result["issues"]) if result["issues"] else "no issues"

    return {
        **state,
        "verification_result": result,
        "logs": [f"VERIFY: {status} — {issue_str}"]
    }

def revise_node(state: AgentState) -> AgentState:
    """Prepare for a retry by incrementing counter and logging."""
    new_retry = state["retry_count"] + 1
    return {
        **state,
        "retry_count": new_retry,
        "logs": [f"REVISE: triggering retry attempt #{new_retry}"]
    }

def finalize_node(state: AgentState) -> AgentState:
    """Format the final structured output."""
    classification = state["classification"]
    answer = state["generated_answer"]
    verification = state["verification_result"]

    # If verification failed and retries exhausted, fall back to safe escalation
    if not verification.get("passed", True) and state["retry_count"] >= 1:
        answer = (
            "I apologize, but I cannot generate a fully verified answer based on the available documentation. "
            "Please escalate this to human support with the relevant object IDs, error codes, and timestamps. "
            "Refer to KB-008 for the escalation checklist."
        )
        classification = "escalation"

    # Build sources list
    sources = []
    for doc in state.get("retrieved_docs", [])[:3]:
        sources.append({
            "document": doc["doc_id"],
            "passage": doc.get("header", doc["chunk_id"])[:120]
        })

    # Determine confidence and human requirement
    confidence = 0.85 if verification.get("passed", True) else 0.5
    requires_human = classification in ["escalation", "out_of_scope"] or not verification.get("passed", True)

    reason = f"Classified as {classification}."
    if verification.get("issues"):
        reason += f" Verification issues: {', '.join(verification['issues'])}."
    else:
        reason += " Verification passed."

    output = {
        "classification": classification,
        "answer": answer,
        "sources": sources,
        "confidence": round(confidence, 2),
        "requires_human": requires_human,
        "reason": reason
    }

    return {
        **state,
        "final_output": output,
        "logs": [f"FINALIZE: output ready | class={classification} | human={requires_human}"]
    }

# =============================================================================
# CONDITIONAL ROUTING FUNCTIONS
# These decide which path to take after a node
# =============================================================================

def route_after_triage(state: AgentState) -> str:
    """Route to retrieve (for answerable/escalation) or generate (for clarify/out_of_scope)."""
    c = state["classification"]
    if c in ["answerable", "escalation"]:
        return "retrieve"
    return "generate"

def route_after_verify(state: AgentState) -> str:
    """Route to finalize if passed, revise if failed and retries left, else finalize."""
    if state["verification_result"].get("passed", True):
        return "finalize"
    elif state["retry_count"] < 1:
        return "revise"
    else:
        return "finalize"

# =============================================================================
# BUILD THE GRAPH
# =============================================================================

def build_agent(kb: KnowledgeBase, model_manager: ModelManager):
    """Build and compile the LangGraph workflow."""
    # Initialize components
    classifier = TriageClassifier(model_manager.embedding_model)
    generator = ResponseGenerator(model_manager)
    verifier = Verifier(model_manager.embedding_model)

    # Create the state graph
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("triage", lambda s: triage_node(s, classifier))
    workflow.add_node("retrieve", lambda s: retrieve_node(s, kb))
    workflow.add_node("generate", lambda s: generate_node(s, generator))
    workflow.add_node("verify", lambda s: verify_node(s, verifier))
    workflow.add_node("revise", revise_node)
    workflow.add_node("finalize", finalize_node)

    # Set entry point
    workflow.set_entry_point("triage")

    # Triage → retrieve OR generate (conditional)
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "retrieve": "retrieve",
            "generate": "generate"
        }
    )

    # Retrieve → generate → verify
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", "verify")

    # Verify → finalize OR revise (conditional)
    workflow.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "finalize": "finalize",
            "revise": "revise"
        }
    )

    # Revise → generate (loop back for retry, protected by retry_count)
    workflow.add_edge("revise", "generate")

    # Finalize → END
    workflow.add_edge("finalize", END)

    return workflow.compile()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_agent(question: str, kb: KnowledgeBase, agent) -> Dict:
    """Run the agent on a single question and return the result."""
    initial_state = {
        "question": question,
        "classification": "answerable",
        "retrieved_docs": [],
        "generated_answer": "",
        "verification_result": {},
        "final_output": {},
        "retry_count": 0,
        "logs": []
    }

    result = agent.invoke(initial_state)
    return result


def main():
    print("=" * 60)
    print("  OrbitDesk Support Agent - Local AI Agent Network")
    print("=" * 60)

    # Step 1: Load knowledge base
    kb = KnowledgeBase(kb_dir="knowledge_base")
    kb.load_documents()

    # Step 2: Load models
    model_manager = ModelManager()
    model_manager.load_models()

    # Step 3: Build embedding index
    kb.build_index(model_manager.embedding_model)

    # Step 4: Build the agent graph
    agent = build_agent(kb, model_manager)
    print("[AGENT] Graph compiled and ready!\n")

    # Step 5: Run test cases
    test_questions = [
        "Can a read-only user create API credentials?",
        "My scheduled exports stopped after I changed my workspace timezone. What should I check?",
        "The suggested solution did not work. What information should I collect before escalating?",
        "Write a refund for my subscription.",
        "It's not working",
    ]

    all_results = []

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"QUESTION: {q}")
        print('='*60)

        result = run_agent(q, kb, agent)

        print("\n--- EXECUTION TRACE ---")
        for log in result["logs"]:
            print(f"  → {log}")

        print("\n--- RETRIEVED EVIDENCE ---")
        for doc in result.get("retrieved_docs", [])[:3]:
            print(f"  [{doc['doc_id']}] {doc.get('header', '')[:80]}... (score: {doc['score']:.3f})")

        print("\n--- FINAL OUTPUT ---")
        print(json.dumps(result["final_output"], indent=2))

        all_results.append({"question": q, "output": result["final_output"]})

    # Save results
    with open("sample_outputs.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\n\n[✓] Results saved to sample_outputs.json")


if __name__ == "__main__":
    main()
