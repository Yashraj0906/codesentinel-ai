# 🛡️ CodeSentinel AI — Complete Interview Prep Guide

> **Goal:** Understand every piece so deeply that you can explain it in your sleep.
> **Framework for every answer:** Problem → Approach → Key Decision → Result

---

## 📛 Why the name "CodeSentinel"?

> "A **sentinel** means a guard or watchman. CodeSentinel = a guard that watches your code. It stands guard over your codebase — automatically detecting bugs, scanning for security vulnerabilities, and helping new team members understand the code. The name reflects what it does: it's an AI sentinel that protects code quality."

---

## 📚 Full Forms & Origins — MEMORIZE THESE

| Abbreviation | Full Form | What It Is | Where It Comes From |
|---|---|---|---|
| **AST** | Abstract Syntax Tree | A tree representation of code structure. Python's `import ast` module gives you this parser for free — it's how Python itself reads your code | Built into Python standard library (no install needed) |
| **CWE** | Common Weakness Enumeration | A standardized list of software vulnerability types (like a dictionary of bugs). Each type has an ID (e.g., CWE-89 = SQL Injection) | Maintained by **MITRE Corporation** (same org that makes CVE). Website: cwe.mitre.org |
| **CVE** | Common Vulnerabilities and Exposures | A specific vulnerability in a specific product (different from CWE which is a category) | Also maintained by MITRE |
| **RAG** | Retrieval Augmented Generation | A technique where you first SEARCH a database, then feed the results to an LLM as context | Invented by Facebook AI Research (Meta) in 2020 |
| **LLM** | Large Language Model | AI models like GPT, Llama that understand and generate text | OpenAI, Meta, Google, etc. |
| **GPTQ** | GPT Quantization | A method to compress large models by reducing precision (e.g., 32-bit → 4-bit) | Research paper by Frantar et al. (2023) |
| **LoRA** | Low-Rank Adaptation | A fine-tuning technique that trains only small adapter matrices instead of all parameters | Research paper by Microsoft (Hu et al., 2021) |
| **CORS** | Cross-Origin Resource Sharing | A browser security feature that controls which websites can call your API | Web standard by W3C |
| **ORM** | Object-Relational Mapping | A tool that lets you work with databases using Python objects instead of raw SQL | Concept; SQLAlchemy is the Python implementation |
| **JWT** | JSON Web Token | A token format for authentication — server gives you a token, you send it with every request | RFC 7519 standard |
| **API** | Application Programming Interface | A set of URLs that your backend exposes for the frontend to call | General software concept |
| **CRUD** | Create, Read, Update, Delete | The 4 basic operations you can do on any data | General software concept |
| **TTL** | Time To Live | How long a cached value stays valid before it expires | General computing concept |

---

## 🧰 What Every Technology Does — Simple Explanation

### 1. Docker 🐳
**What it is:** A tool that packages your application + all its dependencies into a "container" — like a box that contains everything needed to run your app.

**Why you need it:** Without Docker, you'd have to manually install PostgreSQL, Redis, Qdrant on your machine. With Docker, you run `docker-compose up` and everything starts automatically.

**In your project:** Runs 5 services in containers:
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database for user accounts and review history |
| Redis | 6379 | Cache for LLM responses |
| Qdrant | 6333 | Vector database for similarity search |
| FastAPI | 8000 | Backend API server |
| Streamlit | 8501 | Frontend web UI |

**🎤 Interview answer:**
> "Docker lets me package the entire application — database, cache, vector store, backend, frontend — into containers. Instead of asking every developer to install 5 different services manually, they just run `docker-compose up` and everything starts. It ensures my app runs the same way on every machine."

---

### 2. Redis
**Full form:** **RE**mote **DI**ctionary **S**erver

**What it is:** An in-memory key-value store. Think of it like a Python dictionary, but it lives as a separate server and persists data even if your app restarts.

**Why you need it:** LLM calls take 2-3 seconds and cost tokens (money). If someone asks the same question twice, why call the LLM again? Store the answer in Redis (takes < 1 millisecond to retrieve).

**How it works in your project:**
```
User asks "How does auth work?"
  → Generate MD5 hash of the question → "abc123"
  → Check Redis: key "codesentinel:onboard_qa:abc123" exists?
    → YES → Return cached answer (< 1ms) ✅
    → NO → Call LLM (2-3 seconds), save answer to Redis with 1-hour TTL
```

**🎤 Interview answer:**
> "Redis is an in-memory cache that sits between my application and the LLM. Every LLM call is expensive — it costs tokens and takes 2-3 seconds. Redis caches the results with a 1-hour TTL, so repeated queries are served in under 1 millisecond. It reduces both cost and latency."

---

### 3. Qdrant
**What it is:** A vector database. Normal databases search by exact values (WHERE name = 'John'). Vector databases search by **similarity** — "find me code that LOOKS LIKE this code."

**Why you need it:** When you want to check if code matches a known vulnerability pattern, you can't use exact match (every code is written differently). You convert code into a vector (list of numbers) and search for similar vectors.

**How it works in your project:**
```
Your code: "query = f'SELECT * FROM users WHERE id = {user_id}'"
  → Embed with BGE-small → [0.12, -0.45, 0.78, ... 384 numbers]
  → Search Qdrant → Top 5 most similar CWE patterns
  → CWE-89 (SQL Injection) has similarity score 0.92
  → Confirmed vulnerability! ✅
```

**Two collections (tables) in Qdrant:**
| Collection | Contains | Used By |
|-----------|----------|---------|
| `cve_vulnerabilities` | 10 CWE vulnerability patterns | Security Scanner |
| `codebase_chunks` | Code chunks from indexed repos | Onboarding Q&A |

**🎤 Interview answer:**
> "Qdrant is a vector database that enables semantic similarity search. I use it for two things: (1) The security scanner stores CWE vulnerability patterns as vectors and searches for code that's similar to known vulnerabilities. (2) The onboarding module stores indexed code chunks and retrieves them when a developer asks a question. It uses cosine similarity on 384-dimensional vectors from BGE-small embeddings."

---

### 4. Groq API (Llama 3.3 70B)
**What is Groq:** A company that makes custom hardware (LPU — Language Processing Unit) specifically designed to run LLMs extremely fast.

**What is Llama 3.3 70B:** An open-source LLM by Meta with 70 billion parameters. Running on Groq, it generates ~500 tokens/second.

**Why Groq over OpenAI:**
| | Groq | OpenAI |
|---|---|---|
| Speed | ~500 tokens/sec | ~50 tokens/sec |
| Cost | Free tier available | Paid from day 1 |
| Model | Open-source (Llama) | Proprietary (GPT) |
| Latency | ~200ms first token | ~500ms first token |

**🎤 Interview answer:**
> "I chose Groq because it runs LLMs on custom LPU hardware that's about 10x faster than GPU-based inference. For a code review tool where developers expect quick feedback, latency matters. Groq also has a free tier for development, and since it runs Llama 3.3 70B which is open-source, there's no vendor lock-in."

---

### 5. BGE-small-en-v1.5 (Embeddings)
**Full name:** BAAI General Embedding — small English version 1.5

**Made by:** BAAI (Beijing Academy of Artificial Intelligence)

**What it does:** Converts text into a list of 384 numbers (a vector). Similar texts produce similar vectors.

**Why this model:**
- Runs **locally** — no API call, no internet needed, no cost
- Only 33 MB — loads fast, uses minimal memory
- 384 dimensions is enough for code similarity (OpenAI uses 1536 — overkill for this)

**Singleton pattern in your code:**
```python
class EmbeddingService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(settings.embedding_model)
        return cls._instance
```
> "The model loads only ONCE and is reused across all requests. This is the Singleton pattern — it prevents loading a 33MB model into memory every time someone makes a request."

---

### 6. FastAPI
**What it is:** A modern Python web framework for building APIs. 

**Why FastAPI over Flask/Django:**
| | FastAPI | Flask | Django |
|---|---|---|---|
| Async support | ✅ Built-in | ❌ No | Partial |
| Auto API docs | ✅ Swagger UI at /docs | ❌ No | ❌ No |
| Type validation | ✅ Pydantic | ❌ Manual | ❌ Manual |
| Speed | Very fast | Slower | Slower |

**🎤 Interview answer:**
> "FastAPI because of three things: (1) Async support — LLM calls take 2-3 seconds, async lets the server handle other requests while waiting. (2) Auto-generated Swagger docs at `/docs` — interviewers and recruiters can test the API without any tool. (3) Pydantic integration for automatic request/response validation."

---

### 7. Streamlit
**What it is:** A Python library that turns Python scripts into web apps. You write Python, it gives you buttons, text inputs, and charts.

**Why Streamlit over React:**
> "For an ML/AI project, Streamlit lets me build a functional UI in 1 file with pure Python. React would require learning JSX, npm, webpack — unnecessary for a proof-of-concept. Streamlit is the industry standard for ML demos."

---

### 8. PostgreSQL
**What it is:** An open-source relational database (stores data in tables with rows and columns).

**In your project:** Stores user accounts, review history, and chat history. Used with **SQLAlchemy** (Python ORM) and **asyncpg** (async PostgreSQL driver).

---

### 9. Pydantic / pydantic-settings
**What it does:** Validates data automatically. In your project, `config.py` uses it to read `.env` file settings with type checking.

```python
class Settings(BaseSettings):
    groq_api_key: str = ""          # Must be string
    llm_temperature: float = 0.1    # Must be float
    max_self_heal_attempts: int = 3  # Must be integer
```
> "If someone sets `llm_temperature = "abc"` in the .env file, Pydantic will throw an error immediately instead of crashing later in a confusing way."

---

## 🎯 The 30-Second Elevator Pitch (CORRECTED)

> *"CodeSentinel AI is an AI-powered code review platform with two modules. The first module takes code, detects bugs using a two-layer approach — fast static pattern matching for 6 common vulnerability types plus LLM deep analysis for complex logic errors — scans for security vulnerabilities using RAG on a CWE database, generates auto-fixes, and tests them in a sandbox with a self-healing retry loop up to 3 attempts. The second module lets you connect a GitHub repo, indexes it using AST-based chunking, builds a function call graph, and lets new developers ask questions in plain English with answers referencing exact files and line numbers. Currently the static patterns and AST parsing are Python-focused, but the LLM layer works on any language, and I've planned multi-language support using tree-sitter."*

---

## 📖 Stage-by-Stage Deep Dive

### Module 1: Code Review Agent (6 stages)

---

### Stage 1: PARSE — `diff_analyzer.py`

**Problem:** You receive raw code. You can't analyze the whole file — you need individual functions.

**Approach:** Use Python's `ast` (Abstract Syntax Tree) module to break code into functions.

**Key Decision:** Why AST instead of regex?
- Regex can't understand code structure (nested functions, decorators, multiline strings)
- AST actually **parses** Python like the interpreter does — it understands what's a function, what's a class, what's an argument
- AST gives you line numbers, function names, and arguments for free

**Result:** A `DiffAnalysis` object containing a list of `FunctionChange` objects, each with the function name, code, file path, and line numbers.

**Language support:**
- Line 68 of diff_analyzer.py: `if file_path.endswith(".py")` — currently only processes `.py` files
- If AST parsing fails (e.g., non-Python code), the code is still analyzed as a raw chunk by the LLM

**🎤 If interviewer asks:** *"What is AST?"*
> "AST stands for Abstract Syntax Tree. When Python runs your code, the first thing it does is parse it into a tree structure. For example, `def add(a, b): return a + b` becomes a tree with a FunctionDef node, two argument nodes, and a Return node. Python's `ast` module lets me use this same parser. I walk this tree to extract individual functions for analysis."

---

### Stage 2: DETECT — `bug_detector.py`

**Problem:** Need to find bugs in code, but LLM calls are expensive and slow.

**Approach:** Two-layer detection:
- **Layer 1 (Static Patterns):** 6 regex/AST pattern matchers — FREE and INSTANT
- **Layer 2 (LLM Analysis):** For complex bugs that patterns can't catch

**Layer 1 — The 6 Static Detectors:**

| # | Detector | How It Works | CWE | What It Catches |
|---|----------|-------------|-----|-----------------|
| 1 | SQL Injection | Regex finds `f"SELECT ... {var}"` | CWE-89 | User input in SQL queries |
| 2 | Hardcoded Secrets | Regex finds `password = "abc123"` | CWE-798 | Passwords/API keys in code |
| 3 | Command Injection | Regex finds `os.system()`, `eval()`, `exec()` | CWE-78/94 | Dangerous function calls |
| 4 | Bare Except | AST finds `except:` without exception type | CWE-396 | Silent error swallowing |
| 5 | Resource Leak | Finds `f = open()` without `with` | CWE-404 | Files not properly closed |
| 6 | Mutable Default | AST finds `def func(items=[])` | — | Shared mutable default args |

**Layer 2 — LLM Analysis:**
- Sends function code to Llama 3.3 70B via Groq API
- Asks specifically for: logic errors, edge cases, race conditions, performance issues
- Uses `json_mode=True` so LLM returns structured JSON
- Only reports bugs with confidence > 0.7 (reduces false positives)
- Skips functions with < 30 characters (too small to analyze)

**Key Decision:** Why two layers instead of just LLM?
> "Three reasons: (1) **Cost** — static patterns are free, LLM calls cost tokens. For a production tool running on every commit, this matters. (2) **Speed** — regex takes milliseconds, LLM takes 2-3 seconds. (3) **Reliability** — regex has 100% precision for known patterns, LLM can hallucinate. The two layers complement each other — Layer 1 is the fast safety net, Layer 2 catches what patterns miss."

**Deduplication:** After both layers run, results are deduplicated by (bug_type, file_path, line_number) to avoid reporting the same bug twice.

---

### Stage 3: SCAN — `security_scanner.py`

**Problem:** Need to check if code matches known vulnerability patterns from a database.

**Approach:** RAG (Retrieval Augmented Generation)
1. Embed the code using BGE-small → 384-dim vector
2. Search Qdrant `cve_vulnerabilities` collection for top-5 similar CWE patterns
3. Filter results with similarity score < 0.3 (too different, ignore)
4. LLM confirms each match: "Is this code ACTUALLY vulnerable?"

**Where does the CWE data come from?**
> "The CWE data is from MITRE's Common Weakness Enumeration — it's the industry standard catalog of vulnerability types. I've manually curated 10 critical CWE entries in `seed_cve_data.py`. Each entry contains: the CWE ID, a text description of the vulnerability, example vulnerable code patterns, and suggested fixes. This gets embedded and stored in Qdrant."

**The 10 CWE entries in your database:**

| CWE ID | Name | Severity |
|--------|------|----------|
| CWE-89 | SQL Injection | Critical |
| CWE-79 | Cross-site Scripting (XSS) | High |
| CWE-78 | OS Command Injection | Critical |
| CWE-22 | Path Traversal | High |
| CWE-798 | Hardcoded Credentials | Critical |
| CWE-502 | Insecure Deserialization | Critical |
| CWE-20 | Improper Input Validation | High |
| CWE-287 | Improper Authentication | Critical |
| CWE-862 | Missing Authorization | Critical |
| CWE-918 | Server-Side Request Forgery (SSRF) | High |

**Key Decision:** Why RAG instead of just sending all CWEs to the LLM?
> "If I sent all 10+ CWE descriptions with every code snippet, the prompt would be massive — wasting tokens and money. With RAG, I only send the 5 most relevant CWEs, reducing prompt size by 50%+. This also scales — when I add 1000+ CWEs, the LLM prompt stays the same size."

**Key Decision:** Why LLM confirmation after vector search?
> "Vector search finds SIMILAR patterns but can't confirm if the code is actually vulnerable. For example, a parameterized SQL query looks similar to a SQL injection pattern in vector space, but it's actually safe. The LLM acts as a judge — it reads the actual code and says yes/no. This reduces false positives."

**🎤 If interviewer asks:** *"What is RAG?"*
> "RAG stands for Retrieval Augmented Generation. Instead of relying only on what the LLM knows, I first RETRIEVE relevant information from a database — in my case, CWE vulnerability patterns from Qdrant — then AUGMENT the LLM's prompt with that retrieved context, and the LLM GENERATES an answer using both its own knowledge and the retrieved context. It's like giving a student a reference book before asking a question."

---

### Stage 4: FIX — `fix_generator.py`

**Problem:** Bugs detected. Now generate fixes automatically.

**Approach:** Two strategies:
- **Template fixes** for common bugs (e.g., replace `except:` with `except Exception as e:`)
- **LLM-generated fixes** for complex bugs

**Result:** A `CodeFix` object containing: original buggy code, fixed code, explanation, and confidence score.

---

### Stage 5: TEST — `test_runner.py` (⭐ The Self-Healing Loop)

**Problem:** LLM-generated fixes might be wrong. How to verify?

**Approach:** Self-healing loop with maximum 3 attempts:

```
Fix generated → Run in sandbox → Tests pass? → DONE ✅
                                     ↓ NO
                          Send error to LLM →
                          "Your fix caused TypeError on line 5" →
                          LLM generates revised fix →
                          Run again → Tests pass? → DONE ✅
                                          ↓ NO
                                   Last attempt failed →
                                   "Needs human review" ⚠️
```

**Key Technical Details:**
- Tests run in a **subprocess** (separate process, not `exec()`) — isolated from main app
- 30-second timeout to catch infinite loops
- Uses `tempfile.mkdtemp()` — creates a temporary directory that's cleaned up afterward
- If no test provided, LLM auto-generates a pytest test
- `shutil.rmtree()` in `finally` block ensures cleanup even if code crashes

**Key Decision:** Why subprocess instead of `exec()`?
> "Security. If someone submits malicious code and I run it with `exec()`, it runs in MY process — it could delete files, steal environment variables, crash the server. With `subprocess.run()`, it runs in a completely separate process with a 30-second timeout. Even if the code has an infinite loop, my server is safe."

**🎤 If interviewer asks:** *"What if all 3 attempts fail?"*
> "Then the fix is marked as 'needs human review'. The report includes the full heal log showing what was tried and what went wrong at each step, so the developer has context. The system is honest — it doesn't pretend a broken fix works."

---

### Stage 6: REPORT — `report_generator.py`

**Problem:** Present results in a useful format.

**Result:** Both JSON (for API consumers) and Markdown (for humans) with:
- Bug count by severity (critical/high/medium)
- Each bug with description, fix, confidence score
- Cost tracking (tokens used, USD cost)
- Latency metrics (how long each stage took)

---

### Module 2: Codebase Onboarding Agent (6 stages)

---

### Stage 1: INDEX — `repo_indexer.py`
Clones a GitHub repo using the GitHub token and orchestrates the indexing pipeline.

### Stage 2: CHUNK — `code_chunker.py`
Uses AST to split code into meaningful chunks. Each function/class = 1 chunk with metadata (file path, line numbers, function name).

**Key Decision:** Why AST-based chunking instead of fixed-size text splits?
> "If you split code every 500 characters, you'll cut functions in half — making them useless. AST-based chunking respects code boundaries. Each chunk is a complete function or class, so when retrieved during Q&A, the LLM gets meaningful, complete code."

### Stage 3: GRAPH — `graph_builder.py`
Analyzes which functions call which other functions and builds a call graph.

**Why it matters:** When someone asks "how does authentication work?", the system doesn't just find the auth function — it also returns everything that CALLS it and everything IT calls. You get the full picture.

### Stage 4: DOCUMENT — `auto_documenter.py`
LLM generates 1-2 sentence summaries for each code chunk. These summaries are stored in Qdrant as metadata alongside the code.

### Stage 5: STORE — `vector_store.py`
Embeds each chunk with BGE-small and stores vectors + metadata in Qdrant's `codebase_chunks` collection.

### Stage 6: ANSWER — `qa_agent.py`
The Q&A RAG pipeline:
1. Check Redis cache first — if same question was asked before, return cached answer
2. Embed the question with BGE-small
3. Search Qdrant `codebase_chunks` for top-10 relevant chunks
4. Build context with: code text + file paths + line numbers + function summaries + call graph
5. LLM generates answer referencing exact files and line numbers
6. Cache the answer in Redis (1-hour TTL)

---

## 🏗️ Architecture Decisions Summary

| Decision | Chose | Over | Why |
|----------|-------|------|-----|
| LLM | Groq (Llama 3.3 70B) | OpenAI GPT-4 | 10x faster inference, free tier, open-source model |
| Embeddings | BGE-small (local) | OpenAI Ada | Free, no latency, works offline, 33MB only |
| Vector DB | Qdrant (Docker) | Pinecone/ChromaDB | Local, metadata filtering, scales well |
| Cache | Redis | Python dict | Persistent across restarts, shared across processes |
| Backend | FastAPI | Flask/Django | Async, auto Swagger docs, Pydantic validation |
| Frontend | Streamlit | React | Python-native, rapid prototyping for ML apps |
| Database | PostgreSQL | SQLite/MongoDB | ACID compliance, async support, industry standard |
| Sandbox | subprocess | exec() | Security isolation, timeout, separate process |
| Chunking | AST-based | Text splitting | Respects code boundaries, preserves functions |
| Bug detection | Two-layer | LLM-only | Cost + speed + reliability |
| Deployment | Docker Compose | Manual | One command, reproducible, 5 services |
| Config | pydantic-settings | os.environ | Type validation, default values, .env file support |

---

## ⚠️ Language Support — What to say honestly

| Component | Any Language? | Why |
|-----------|--------------|-----|
| Static Pattern Detection (Layer 1) | ❌ Python only | Uses Python's `ast` module and Python-specific regex |
| LLM Deep Analysis (Layer 2) | ✅ Any language | Llama can understand Java, Rust, Go, etc. |
| Security Scanner (RAG) | ✅ Any language | Vector similarity is language-agnostic |
| AST Parsing (diff_analyzer) | ❌ Python only | `ast.parse()` only parses Python syntax |
| Code Chunking (onboarding) | ❌ Python only | Uses Python AST for function extraction |
| Q&A Agent | ✅ Any language | LLM can answer about any code |

**What to say:**
> "Currently, the static pattern layer and AST parsing are Python-specific because I used Python's built-in `ast` module. But the LLM analysis layer and RAG security scanner work on any language since they're language-agnostic. For multi-language support, I've planned to replace Python's `ast` with **tree-sitter**, which is a universal parser supporting 40+ languages."

---

## 🎤 Top 15 Interview Questions & Answers

### Q1: "Tell me about your project."
> *Use the 30-second elevator pitch from above.*

### Q2: "Why the name CodeSentinel?"
> "Sentinel means a guard or watchman. CodeSentinel is an AI guard that watches your code — detecting bugs, scanning for security vulnerabilities, and helping onboard new developers."

### Q3: "What problem does it solve?"
> "Two problems: (1) Code reviews are slow — a senior developer takes 30-60 minutes per PR. My tool gives instant feedback on common bugs and security issues. (2) Onboarding — when a new developer joins, it takes weeks to understand the codebase. My tool lets them ask questions in plain English and get answers with exact file and line references."

### Q4: "Why two layers for bug detection?"
> "Cost, speed, and reliability. Static patterns are free and instant with 100% precision. LLM catches what patterns miss but costs tokens and takes 2-3 seconds. Using both gives the best of both worlds."

### Q5: "What is RAG and how do you use it?"
> "RAG = Retrieval Augmented Generation. I retrieve the 5 most relevant CWE vulnerability patterns from Qdrant using vector similarity, then augment the LLM's prompt with these patterns, and the LLM generates a judgment — is this code actually vulnerable? It's like giving a doctor a patient's medical history before asking for a diagnosis."

### Q6: "How does the self-healing work?"
> "When a fix is generated, it's tested in a sandboxed subprocess. If tests fail, the error message is sent back to the LLM: 'your fix caused TypeError on line 5, try again.' The LLM generates a revised fix. This loops up to 3 times. It's similar to how a developer debugs — try, fail, read error, adjust."

### Q7: "What are your benchmark results?"
> "On the static pattern layer, I achieved 100% precision and 100% recall across 10 test cases — zero false positives, zero false negatives. Every real bug was found and no clean code was wrongly flagged."

### Q8: "What's the difference between precision and recall?"
> "Precision = of all bugs I REPORTED, how many were REAL bugs (not false alarms). Recall = of all ACTUAL bugs in the code, how many did I FIND. Precision answers 'can I trust the results?' Recall answers 'did I miss anything?'"

### Q9: "Why Qdrant over Pinecone?"
> "Qdrant runs locally as a Docker container — no cloud account, no API limits, no cost. It supports metadata filtering for filtering by severity. Pinecone is cloud-only and costs money."

### Q10: "Why Groq over OpenAI?"
> "Speed. Groq runs on custom LPU hardware — about 500 tokens/second vs OpenAI's ~50 tokens/second. For a code review tool where developers want quick feedback, latency matters. Plus Groq has a free tier."

### Q11: "What does Docker do in your project?"
> "Docker packages each service — PostgreSQL, Redis, Qdrant, FastAPI, Streamlit — into isolated containers. Instead of installing 5 services manually, you run `docker-compose up` and everything starts with correct ports and connections. It also ensures the app runs identically on any machine."

### Q12: "What does Redis do?"
> "Redis caches LLM responses. LLM calls take 2-3 seconds and cost tokens. If someone asks the same question twice, Redis returns the cached answer in under 1 millisecond. The cache has a 1-hour TTL so stale answers eventually expire."

### Q13: "How does codebase Q&A work?"
> "I index the repo by parsing every file with AST, creating chunks per function, embedding them with BGE-small, and storing in Qdrant. When someone asks a question, I embed it, search Qdrant for the 10 most similar chunks, build context with code + summaries + call graph, and LLM answers referencing specific files and lines."

### Q14: "What would you improve?"
> "Four things: (1) Multi-language support using tree-sitter parser. (2) GitHub webhook integration so it auto-reviews every PR. (3) Expand CWE database from 10 to 1000+ entries. (4) Deploy to cloud with CI/CD pipeline."

### Q15: "Why not just use ChatGPT/Copilot?"
> "Three reasons: (1) **Domain-specific** — my tool has a curated CWE database for security scanning, ChatGPT doesn't. (2) **Self-healing** — my tool tests fixes in a sandbox and retries if they fail, ChatGPT just suggests. (3) **Codebase-aware** — the onboarding module indexes YOUR specific repo, it's not generic answers."

---

## 🚀 Quick Reference Card (MEMORIZE THIS)

```
CodeSentinel AI = Code Review Agent + Codebase Onboarding Agent
Name = "Sentinel" means guard → AI guard for code

CODE REVIEW PIPELINE (6 stages):
  Parse (AST) → Detect (regex + LLM) → Scan (RAG on CWE) → 
  Fix (template + LLM) → Test (sandbox + self-heal x3) → Report

ONBOARDING PIPELINE (6 stages):
  Clone repo → Chunk (AST) → Build call graph → Document (LLM) → 
  Store in Qdrant → Answer questions (RAG)

TECH STACK:
  LLM      = Groq API + Llama 3.3 70B (fastest LLM inference)
  Embed    = BGE-small-en (384-dim, runs locally, free)
  VectorDB = Qdrant (Docker, cosine similarity)
  Cache    = Redis (cache LLM calls, 1-hour TTL)
  Backend  = FastAPI (async, auto Swagger docs)
  Frontend = Streamlit (Python-native UI)
  Database = PostgreSQL (users, review history)
  Deploy   = Docker Compose (5 services, 1 command)
  Config   = pydantic-settings (reads .env with type checking)

KEY NUMBERS:
  6 static bug detectors (free, instant)
  10 CWE entries in vulnerability database
  3 max self-heal retry attempts
  30s sandbox timeout
  384-dimensional embedding vectors
  Top-5 CWE results for security scan
  Top-10 code chunks for Q&A
  1-hour Redis cache TTL
  100% precision & recall on 10 benchmarks

FULL FORMS:
  AST = Abstract Syntax Tree (Python's code parser)
  CWE = Common Weakness Enumeration (by MITRE)
  RAG = Retrieval Augmented Generation
  LLM = Large Language Model
  TTL = Time To Live (cache expiry)
  CORS = Cross-Origin Resource Sharing
  JWT = JSON Web Token
  ORM = Object-Relational Mapping
  CRUD = Create, Read, Update, Delete
```

---

> [!TIP]
> **Confidence tip:** When answering, follow this 4-step pattern:
> 1. **State the problem** (1 sentence)
> 2. **State your approach** (1-2 sentences)
> 3. **Explain WHY you chose it** (1 sentence with comparison)
> 4. **Give the result** (1 sentence)
>
> Example: "The problem was expensive LLM calls. So I added Redis caching. I chose Redis over a Python dict because Redis persists across restarts and is shared across processes. Now repeated queries are served in under 1 millisecond."

> [!IMPORTANT]
> **Before every interview, read through the Quick Reference Card 3 times.** That's all you need to remember. Everything else you can derive from understanding the pipeline.
