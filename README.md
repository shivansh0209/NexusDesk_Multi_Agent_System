# NexusDesk — Multi-Agent Customer Support System

> A production-grade multi-agent AI system built on LangChain — deliberately without LangGraph — to demonstrate why orchestration frameworks exist.

---

## What Is NexusDesk?

NexusDesk is an intelligent customer support platform for **FlowDesk**, a fictional project management SaaS. It receives a raw customer query, runs it through a pipeline of specialized AI agents, and either resolves it autonomously or routes it to a human agent with a pre-packaged briefing.

The system is powered by **Gemini 2.5 Flash**, **LangChain**, and **ChromaDB**, and is structured across three layers of agents with distinct responsibilities.

---

## Why I Built This

This project was built with a specific purpose: **to bridge the gap between LangChain-LangGraph and to enter bit of professionalism**

LangGraph is a powerful orchestration framework built on top of LangChain for managing stateful, multi-agent workflows. But its value is hard to appreciate until you have felt the pain it solves.

NexusDesk is that pain — deliberately.

The flow here is relatively straightforward: three agents in Layer 1, three in Layer 2, two supervisors, and a human handoff layer. And yet, look at the orchestration code required to wire it together cleanly — the routing logic, the fallback handling, the non-fatal error paths, the state passing between agents, the layered supervision decisions.

**If a simple linear flow like this already demands this much orchestration code, imagine what a system with cycles, retries, parallel fan-outs, and dynamic agent selection would look like in plain Python.**

That is exactly the gap LangGraph fills. NexusDesk was built to make that argument tangible.

---

## Architecture

````mermaid
flowchart TD
    Q([Customer Query]) --> L1

    subgraph L1[Layer 1 — Context & Intelligence]
        A1[Intent Analyzer Agent] --> A2[Context Builder Agent] --> A3[Query Synthesizer Agent] --> S1[Layer 1 Supervisor]
    end

    S1 -->|P0 or critical flags| L3
    S1 -->|Selects agents to invoke in L2| L2

    subgraph L2[Layer 2 — Resolution]
        B1[Knowledge Base Agent] --> B3[Action & Response Agent]
        B2[Policy & Eligibility Agent] --> B3
        B3 --> S2[Layer 2 Supervisor]
    end

    S2 -->|Low confidence or requires human| L3
    S2 -->|Resolved| R([Customer Response ✓])

    subgraph L3[Layer 3 — Human Handoff]
        H[Priority-Routed Briefing + Draft]
    end
````

---

## Project Highlights

### Production-Grade Code Structure
```text
NexusDesk/
├── main.py                        # Orchestration pipeline
├── src/
│   ├── agents/
│   │   ├── level_1/               # Intent, Context, Synthesis, L1 Supervisor
│   │   └── level_2/               # KB, Policy, Action, L2 Supervisor
│   ├── models/                    # Pydantic models for every agent I/O
│   ├── prompts/                   # LangChain prompt templates, one per agent
│   └── utils/                     # Data preprocessing, embeddings, logger
├── data/
│   ├── knowledge_base/            # Simulated company data (policies, profiles, tickets)
│   └── processed/                 # Preprocessed and normalized for ChromaDB
└── tests/                         # Full unit test suite with mocked LLM responses
│
└── logs/      
```

Every layer is isolated. Every agent has its own model, prompt, and function. Module-level LLM clients use the `_` prefix convention and are instantiated once — not on every call.

### Professional Error Handling
- `ValueError` (domain errors: inactive account, empty query, customer not found) is caught and returned cleanly.
- Agent failures in Layer 2 are **non-fatal** — if the KB Agent crashes, the pipeline continues on the Policy result alone.
- If both upstream agents fail, the system falls back to a human handoff rather than crashing.
- All errors are logged via Python's `logging` module — no bare `print()` statements anywhere.

### Full Test Suite with Mocked LLM Responses
All 8 agents and the full orchestration pipeline are covered by unit tests using Python's `unittest.mock`. LLM API calls are patched entirely — tests run instantly with no API key and no cost.

Tests cover:
- Happy path resolution
- P0 and critical flag escalation from Layer 1 Supervisor
- Low confidence escalation from Layer 2 Supervisor
- Non-fatal KB/Policy agent failure handling
- Domain error paths (inactive accounts, missing customers)

### ChromaDB with Metadata Filtering
Rather than FAISS, ChromaDB was chosen specifically for its support for **heavy metadata filtering** — filtering tickets by category and subscription tier before semantic ranking. Data is batch-upserted using a generalized preprocessing pipeline that normalizes raw company data into a consistent `{id, content, metadata}` format.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Gemini 2.5 Flash via `langchain-google-genai` |
| Orchestration | LangChain (LCEL chains, structured output) |
| Vector Store | ChromaDB with SentenceTransformers embeddings |
| Data Validation | Pydantic v2 |
| Testing | pytest + unittest.mock |
| Logging | Python logging module |

---

## Running the Project

**Install dependencies**
```bash
pip install langchain-google-genai langchain-core chromadb sentence-transformers pydantic
pip install pytest
```

**Set your API key**
```bash
export GOOGLE_API_KEY=your_key_here
```

**Preprocess and embed data**
```bash
python src/utils/data_preprocessing.py
python src/utils/embedding_function.py
```

**Run the pipeline**
```bash
python main.py CUST_001 "I was charged twice and have a demo tomorrow"
```

**Run tests**
```bash
python -m pytest tests/ -v -s
```

---

## The Takeaway

NexusDesk is not a complex graph. It has no cycles, no parallel fan-outs, no dynamic agent spawning. It is a straightforward linear flow with two routing decisions.

And it still required a non-trivial amount of orchestration code to handle correctly.

That is the point.

> *If this much orchestration code is needed for a simple flow — imagine what a production system with retries, cycles, and dynamic agent selection would look like without a framework built for it.*

That is what LangGraph solves. NexusDesk was built to make you feel why.