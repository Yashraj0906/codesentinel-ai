# CodeSentinel AI — Architecture Overview

## The Big Picture

```mermaid
graph TB
    USER["👤 User"] --> |"Pastes code / diff"| UI["🖥️ Streamlit UI<br/>ui/streamlit_app.py"]
    USER --> |"Connects GitHub repo"| UI
    
    UI --> |"HTTP requests"| API["⚡ FastAPI Backend<br/>src/api/main.py"]
    
    API --> MODULE1["🔍 Module 1<br/>Code Review"]
    API --> MODULE2["📚 Module 2<br/>Codebase Onboarding"]
    
    MODULE1 --> REPORT["📊 Review Report"]
    MODULE2 --> ANSWER["💬 Answer with<br/>code references"]
    
    REPORT --> UI
    ANSWER --> UI

    style USER fill:#4CAF50,color:#fff
    style UI fill:#2196F3,color:#fff
    style API fill:#FF9800,color:#fff
    style MODULE1 fill:#9C27B0,color:#fff
    style MODULE2 fill:#009688,color:#fff
    style REPORT fill:#E91E63,color:#fff
    style ANSWER fill:#00BCD4,color:#fff
```

---

## Module 1: Code Review Pipeline

```mermaid
graph LR
    CODE["Code Input"] --> DA["diff_analyzer.py<br/>──────────<br/>Parses code<br/>Extracts functions<br/>using AST"]
    
    DA --> BD["bug_detector.py<br/>──────────<br/>Layer 1: 6 static<br/>pattern checks<br/>Layer 2: LLM analysis"]
    
    DA --> SS["security_scanner.py<br/>──────────<br/>Embeds code →<br/>Searches Qdrant →<br/>LLM confirms vuln"]
    
    BD --> FG["fix_generator.py<br/>──────────<br/>Template fixes<br/>+ LLM fixes"]
    SS --> FG
    
    FG --> TR["test_runner.py<br/>──────────<br/>Runs fix in sandbox<br/>Tests pass? → Done<br/>Tests fail? → Retry"]
    
    TR --> |"Self-heal loop<br/>max 3 attempts"| FG
    
    TR --> RG["report_generator.py<br/>──────────<br/>JSON + Markdown<br/>report with costs"]

    style CODE fill:#424242,color:#fff
    style DA fill:#7B1FA2,color:#fff
    style BD fill:#C62828,color:#fff
    style SS fill:#E65100,color:#fff
    style FG fill:#2E7D32,color:#fff
    style TR fill:#1565C0,color:#fff
    style RG fill:#00838F,color:#fff
```

---

## Module 2: Codebase Onboarding Pipeline

```mermaid
graph LR
    REPO["GitHub Repo URL"] --> RI["repo_indexer.py<br/>──────────<br/>Clones repo<br/>Orchestrates indexing"]
    
    RI --> CC["code_chunker.py<br/>──────────<br/>AST-based chunking<br/>Each function = 1 chunk<br/>Extracts metadata"]
    
    CC --> VS2["vector_store.py<br/>──────────<br/>Embeds chunks →<br/>Stores in Qdrant"]
    
    CC --> GB["graph_builder.py<br/>──────────<br/>Builds call graph<br/>func → calls → deeper"]
    
    CC --> AD["auto_documenter.py<br/>──────────<br/>LLM summarizes each<br/>function + module"]
    
    QUESTION["❓ User Question"] --> QA["qa_agent.py<br/>──────────<br/>Searches Qdrant →<br/>Traces call graph →<br/>LLM answers with<br/>code references"]
    
    VS2 --> QA
    GB --> QA
    AD --> QA

    style REPO fill:#424242,color:#fff
    style QUESTION fill:#4CAF50,color:#fff
    style RI fill:#6A1B9A,color:#fff
    style CC fill:#AD1457,color:#fff
    style VS2 fill:#E65100,color:#fff
    style GB fill:#1B5E20,color:#fff
    style AD fill:#0D47A1,color:#fff
    style QA fill:#00695C,color:#fff
```

---

## Shared Infrastructure (used by both modules)

```mermaid
graph TB
    subgraph SHARED ["src/shared/ — Used by everything"]
        LLM["llm_client.py<br/>Talks to Groq API"]
        EMB["embeddings.py<br/>Text → Vectors"]
        VS["vector_store.py<br/>Qdrant read/write"]
        CACHE["cache.py<br/>Redis caching"]
        COST["cost_tracker.py<br/>Tracks money spent"]
    end
    
    subgraph INFRA ["External Services via Docker"]
        GROQ["☁️ Groq API"]
        QD["🔷 Qdrant :6333"]
        RD["🔴 Redis :6379"]
        PG["🐘 PostgreSQL :5432"]
    end
    
    LLM --> GROQ
    LLM --> COST
    VS --> QD
    VS --> EMB
    CACHE --> RD

    CONFIG["config.py<br/>All settings from .env"] --> LLM
    CONFIG --> VS
    CONFIG --> CACHE

    style SHARED fill:#1A237E,color:#fff
    style INFRA fill:#263238,color:#fff
    style CONFIG fill:#FF6F00,color:#fff
```

---

## Complete File Map

```
📁 codesentinel-ai/
│
├── 📄 .env                    ← Your secrets (API keys)
├── 📄 pyproject.toml          ← Dependencies
├── 📄 docker-compose.yml      ← One command to run everything
├── 📄 Dockerfile              ← Package the app
│
├── 📁 src/
│   ├── 📄 config.py           ← All settings loaded from .env
│   │
│   ├── 📁 shared/             ← Used by BOTH modules
│   │   ├── 📄 llm_client.py       → Groq API wrapper + retry + cost
│   │   ├── 📄 embeddings.py       → Text → 384-dim vector
│   │   ├── 📄 vector_store.py     → Qdrant CRUD operations
│   │   ├── 📄 cache.py            → Redis get/set with TTL
│   │   └── 📄 cost_tracker.py     → Tracks tokens + cost + latency
│   │
│   ├── 📁 review/             ← MODULE 1: Code Review
│   │   ├── 📄 diff_analyzer.py    → Parses code, extracts functions (AST)
│   │   ├── 📄 bug_detector.py     → 6 static patterns + LLM analysis
│   │   ├── 📄 security_scanner.py → RAG on CWE vulnerability database
│   │   ├── 📄 fix_generator.py    → Generates code fixes
│   │   ├── 📄 test_runner.py      → Runs tests + self-healing loop
│   │   └── 📄 report_generator.py → Builds JSON + Markdown report
│   │
│   ├── 📁 onboard/            ← MODULE 2: Codebase Onboarding
│   │   ├── 📄 repo_indexer.py     → Clones + orchestrates indexing
│   │   ├── 📄 code_chunker.py     → AST-based code chunking
│   │   ├── 📄 graph_builder.py    → Builds function call graph
│   │   ├── 📄 auto_documenter.py  → LLM-generated summaries
│   │   └── 📄 qa_agent.py         → Answers questions about codebase
│   │
│   ├── 📁 api/                ← FastAPI Backend
│   │   ├── 📄 main.py             → App entry point + CORS + routes
│   │   ├── 📁 routes/             → review, onboard, auth, health
│   │   └── 📁 middleware/         → rate_limiter, auth
│   │
│   ├── 📁 db/                 ← Database
│   │   ├── 📄 database.py         → SQLAlchemy connection
│   │   └── 📄 models.py           → Users, Reviews, ChatHistory
│   │
│   └── 📁 evaluation/         ← Benchmarks
│       ├── 📄 metrics.py          → Precision, Recall, F1
│       └── 📄 benchmark.py        → Run eval on 50+ test cases
│
├── 📁 ui/
│   └── 📄 streamlit_app.py    ← Frontend (2 tabs)
│
├── 📁 scripts/
│   ├── 📄 seed_cve_data.py        → Load CWE data into Qdrant
│   └── 📄 run_benchmarks.py       → Run evaluation suite
│
└── 📁 data/
    ├── 📁 cve_data/               → CWE/OWASP vulnerability data
    └── 📁 eval/                   → Test cases for benchmarks
```

---

## Build Order

```mermaid
graph LR
    P1["Phase 1<br/>Foundation<br/>config + shared/"] --> P2["Phase 2<br/>Diff Analyzer<br/>+ Bug Detector"]
    P2 --> P3["Phase 3<br/>Security Scanner<br/>RAG on CWE"]
    P3 --> P4["Phase 4<br/>Fix Generator<br/>+ Self-Heal Loop"]
    P4 --> P5["Phase 5<br/>Onboarding Agent<br/>chunker + QA"]
    P5 --> P6["Phase 6<br/>FastAPI + DB<br/>+ Auth"]
    P6 --> P7["Phase 7<br/>Streamlit UI"]
    P7 --> P8["Phase 8<br/>Docker Compose"]
    P8 --> P9["Phase 9<br/>Eval + Benchmarks"]

    style P1 fill:#4CAF50,color:#fff
    style P2 fill:#4CAF50,color:#fff
    style P3 fill:#FF9800,color:#fff
    style P4 fill:#FF9800,color:#fff
    style P5 fill:#2196F3,color:#fff
    style P6 fill:#9C27B0,color:#fff
    style P7 fill:#E91E63,color:#fff
    style P8 fill:#607D8B,color:#fff
    style P9 fill:#795548,color:#fff
```

> 🟢 Green = Done | 🟠 Orange = Next | 🔵 Blue = Later
