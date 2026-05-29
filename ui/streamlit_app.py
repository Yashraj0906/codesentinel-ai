# ============================================================
# streamlit_app.py -- Premium Frontend UI
# ============================================================
# HOW TO RUN:
#   streamlit run ui/streamlit_app.py
# ============================================================

import streamlit as st
import httpx
import time

# Page config
st.set_page_config(
    page_title="CodeSentinel AI",
    page_icon="https://img.icons8.com/fluency/48/shield.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# API base URL
API_URL = "http://localhost:8000"

# ── Custom CSS for premium look ──
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e);
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0;
    }
    .sub-header {
        color: #8892b0;
        font-size: 1.1rem;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #667eea;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #e2e8f0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Severity badges */
    .badge-critical { 
        background: linear-gradient(135deg, #dc2626, #991b1b); 
        color: white; padding: 4px 12px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600; display: inline-block;
    }
    .badge-high { 
        background: linear-gradient(135deg, #ea580c, #c2410c); 
        color: white; padding: 4px 12px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600; display: inline-block;
    }
    .badge-medium { 
        background: linear-gradient(135deg, #d97706, #b45309); 
        color: white; padding: 4px 12px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600; display: inline-block;
    }
    .badge-low { 
        background: linear-gradient(135deg, #2563eb, #1d4ed8); 
        color: white; padding: 4px 12px; border-radius: 20px; 
        font-size: 0.75rem; font-weight: 600; display: inline-block;
    }
    
    /* Issue cards */
    .issue-card {
        background: #1e293b;
        border-left: 4px solid;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .issue-critical { border-left-color: #dc2626; }
    .issue-high { border-left-color: #ea580c; }
    .issue-medium { border-left-color: #d97706; }
    .issue-low { border-left-color: #2563eb; }
    
    /* Risk level indicator */
    .risk-high { color: #ef4444; font-weight: 700; font-size: 1.2rem; }
    .risk-medium { color: #f59e0b; font-weight: 700; font-size: 1.2rem; }
    .risk-low { color: #22c55e; font-weight: 700; font-size: 1.2rem; }
    
    /* Stats bar */
    .stats-bar {
        background: linear-gradient(90deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px 25px;
        margin: 15px 0;
        display: flex;
        justify-content: space-between;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        border-radius: 8px;
    }
    
    /* Button styling */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #667eea, #764ba2);
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(90deg, #764ba2, #667eea);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Text area styling */
    .stTextArea textarea {
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
        font-size: 0.9rem !important;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #475569;
        padding: 20px 0;
        font-size: 0.8rem;
        border-top: 1px solid #1e293b;
        margin-top: 40px;
    }
    
    /* Powered by badges */
    .tech-badge {
        display: inline-block;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 4px 10px;
        margin: 2px;
        font-size: 0.75rem;
        color: #94a3b8;
    }
</style>
""", unsafe_allow_html=True)


# ── Header ──
st.markdown('<h1 class="main-header">CodeSentinel AI</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered Code Review & Codebase Intelligence Platform</p>', unsafe_allow_html=True)

# Tech badges
st.markdown("""
<div style="margin-bottom: 25px;">
    <span class="tech-badge">Groq LLM</span>
    <span class="tech-badge">Qdrant</span>
    <span class="tech-badge">Redis</span>
    <span class="tech-badge">FastAPI</span>
    <span class="tech-badge">RAG Pipeline</span>
    <span class="tech-badge">Self-Healing</span>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──
tab1, tab2 = st.tabs(["  Code Review  ", "  Codebase Q&A  "])


# ============================================================
# TAB 1: CODE REVIEW
# ============================================================
with tab1:
    # Two columns: code input + example selector
    col_main, col_side = st.columns([3, 1])
    
    with col_side:
        st.markdown("##### Quick Examples")
        example = st.selectbox(
            "Load a test case:",
            [
                "-- Select --",
                "SQL Injection",
                "Hardcoded Secrets",
                "Command Injection", 
                "Multiple Vulnerabilities",
                "Clean Code",
            ],
            label_visibility="collapsed",
        )
        
        examples = {
            "SQL Injection": '''def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)
    return cursor.fetchone()''',
            "Hardcoded Secrets": '''def connect_db():
    password = "super_secret_123"
    api_key = "sk-1234567890abcdef"
    return psycopg2.connect(
        host="localhost",
        password=password,
    )''',
            "Command Injection": '''import os
import subprocess

def ping_host(hostname):
    os.system(f"ping -c 3 {hostname}")
    
def list_files(directory):
    subprocess.call(f"ls {directory}", shell=True)''',
            "Multiple Vulnerabilities": '''def login(username, password):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    api_key = "sk-prod-key-abc123"
    try:
        result = eval(username)
        data = pickle.loads(request.data)
    except:
        pass
    return result''',
            "Clean Code": '''def add_numbers(a: int, b: int) -> int:
    """Add two numbers and return the result."""
    return a + b

def greet(name: str) -> str:
    """Return a greeting message."""
    if not name:
        raise ValueError("Name cannot be empty")
    return f"Hello, {name}!"''',
        }
        
        if example != "-- Select --":
            selected_code = examples[example]
        else:
            selected_code = ""
    
    with col_main:
        code_input = st.text_area(
            "Paste your Python code:",
            value=selected_code,
            height=280,
            placeholder="Paste your Python code here or select an example from the right...",
        )
    
    # Analyze button
    col_btn, col_space = st.columns([1, 4])
    with col_btn:
        review_btn = st.button("Analyze Code", type="primary", use_container_width=True)
    
    if review_btn and code_input.strip():
        progress_bar = st.progress(0, text="Initializing pipeline...")
        
        start_time = time.time()
        
        try:
            progress_bar.progress(10, text="[1/6] Analyzing code structure...")
            
            response = httpx.post(
                f"{API_URL}/review/analyze",
                json={"code": code_input},
                timeout=180.0,
            )
            
            elapsed = time.time() - start_time
            progress_bar.progress(100, text="Review complete!")
            time.sleep(0.5)
            progress_bar.empty()
            
            if response.status_code == 200:
                data = response.json()
                
                # ── Summary Metrics ──
                st.markdown("---")
                st.markdown("### Review Results")
                
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                
                with c1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">{data['total_issues']}</div>
                        <div class="metric-label">Total Issues</div>
                    </div>""", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #ef4444;">{data['critical_count']}</div>
                        <div class="metric-label">Critical</div>
                    </div>""", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #f97316;">{data['high_count']}</div>
                        <div class="metric-label">High</div>
                    </div>""", unsafe_allow_html=True)
                with c4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #eab308;">{data['medium_count']}</div>
                        <div class="metric-label">Medium</div>
                    </div>""", unsafe_allow_html=True)
                with c5:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #22c55e;">{data['issues_auto_fixed']}</div>
                        <div class="metric-label">Auto-Fixed</div>
                    </div>""", unsafe_allow_html=True)
                with c6:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value" style="color: #8b5cf6;">${data['total_cost_usd']:.4f}</div>
                        <div class="metric-label">LLM Cost</div>
                    </div>""", unsafe_allow_html=True)
                
                # Risk level
                risk = data["risk_level"]
                st.markdown(f"""
                <div style="margin: 15px 0; padding: 10px 20px; background: #1e293b; border-radius: 8px; border: 1px solid #334155;">
                    Risk Level: <span class="risk-{risk}">{risk.upper()}</span>
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    Review Time: <strong>{elapsed:.1f}s</strong>
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    Detection: <strong>Static Patterns + LLM + Security RAG</strong>
                </div>
                """, unsafe_allow_html=True)
                
                # ── Detailed Issues ──
                st.markdown("### Detected Issues")
                
                for i, issue in enumerate(data["issues"]):
                    severity = issue["severity"]
                    badge_class = f"badge-{severity}"
                    card_class = f"issue-{severity}"
                    status = "AUTO-FIXED" if issue.get("auto_fixed") else "Needs Review"
                    status_color = "#22c55e" if issue.get("auto_fixed") else "#f59e0b"
                    
                    bug_title = issue['bug_type'].replace('_', ' ').title()
                    
                    with st.expander(
                        f"{'[!]' if severity == 'critical' else '[*]'} {bug_title} -- {issue['file_path']} line {issue.get('line_number', '?')}",
                        expanded=(severity in ["critical"]),
                    ):
                        st.markdown(f"""
                        <span class="{badge_class}">{severity.upper()}</span>
                        <span style="color: {status_color}; margin-left: 10px; font-size: 0.85rem;">{status}</span>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"**What's wrong:** {issue['description']}")
                        st.markdown(f"**How to fix:** {issue['suggestion']}")
                        st.markdown(f"**Detection:** `{issue['detection_method']}` | **Confidence:** `{issue['confidence']:.0%}`")
                        
                        if issue.get("fix") and issue["fix"].get("fixed_code"):
                            st.markdown("**Auto-generated fix:**")
                            st.code(issue["fix"]["fixed_code"], language="python")
                            st.caption(f"Explanation: {issue['fix'].get('explanation', '')}")
                
                # Full report
                with st.expander("View Full Markdown Report"):
                    st.markdown(data["markdown_report"])
                    
            else:
                st.error(f"API returned error {response.status_code}: {response.text[:500]}")
                
        except httpx.ConnectError:
            progress_bar.empty()
            st.error("Cannot connect to the API server. Make sure it's running:\n\n`uvicorn src.api.main:app --port 8000 --reload`")
        except httpx.ReadTimeout:
            progress_bar.empty()
            st.warning("The review is taking longer than expected. The pipeline makes multiple LLM calls which can take 60-90 seconds. Please try again.")
        except Exception as e:
            progress_bar.empty()
            st.error(f"Unexpected error: {e}")
    
    elif review_btn:
        st.warning("Please paste some code or select an example from the dropdown.")


# ============================================================
# TAB 2: CODEBASE Q&A
# ============================================================
with tab2:
    st.markdown("### Codebase Onboarding Agent")
    st.markdown("Index a GitHub repository and ask questions about the code. New joinees can instantly understand any codebase.")
    
    # ── Index a repo ──
    st.markdown("#### Step 1: Index a Repository")
    
    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        repo_url = st.text_input(
            "GitHub Repository URL:",
            placeholder="https://github.com/username/repo",
            label_visibility="collapsed",
        )
    with col2:
        branch = st.text_input("Branch", value="main", label_visibility="collapsed")
    with col3:
        index_btn = st.button("Index Repo", type="primary", use_container_width=True)
    
    if index_btn and repo_url.strip():
        with st.spinner("Cloning and indexing repository..."):
            try:
                response = httpx.post(
                    f"{API_URL}/onboard/index",
                    json={"repo_url": repo_url, "branch": branch},
                    timeout=300.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Files", data['files'])
                    c2.metric("Code Chunks", data['chunks'])
                    c3.metric("Graph Nodes", data['graph_nodes'])
                    c4.metric("Summaries", data['summaries'])
                    st.success("Repository indexed successfully! You can now ask questions below.")
                else:
                    st.error(f"Indexing failed: {response.text[:300]}")
                    
            except httpx.ConnectError:
                st.error("Cannot connect to the API. Make sure the backend is running.")
            except Exception as e:
                st.error(f"Error: {e}")
    
    # ── Ask questions ──
    st.markdown("---")
    st.markdown("#### Step 2: Ask Questions About the Code")
    
    # Quick question buttons
    st.markdown("**Quick questions:**")
    qcol1, qcol2, qcol3 = st.columns(3)
    
    preset_q = None
    with qcol1:
        if st.button("How does the main pipeline work?", use_container_width=True):
            preset_q = "How does the main pipeline work?"
    with qcol2:
        if st.button("What functions handle security?", use_container_width=True):
            preset_q = "What functions handle security?"
    with qcol3:
        if st.button("Show me the database models", use_container_width=True):
            preset_q = "Show me the database models"
    
    question = st.text_input(
        "Ask anything about the codebase:",
        value=preset_q or "",
        placeholder="How does user authentication work?",
    )
    
    ask_btn = st.button("Ask", type="primary")
    
    if (ask_btn or preset_q) and question.strip():
        with st.spinner("Searching codebase..."):
            try:
                response = httpx.post(
                    f"{API_URL}/onboard/ask",
                    json={"question": question},
                    timeout=60.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    st.markdown("### Answer")
                    st.markdown(data["answer"])
                    
                    if data["code_references"]:
                        st.markdown("### Referenced Code")
                        for ref in data["code_references"]:
                            with st.expander(f"{ref['file_path']} -- {ref['name']} (lines {ref['start_line']}-{ref['end_line']})"):
                                st.caption(ref.get("summary", ""))
                                score = ref.get('score', 0)
                                score_color = "#22c55e" if score > 0.7 else "#f59e0b" if score > 0.4 else "#ef4444"
                                st.markdown(f"Relevance: <span style='color:{score_color};font-weight:600;'>{score:.2f}</span>", unsafe_allow_html=True)
                    
                    if data.get("cached"):
                        st.caption("Served from cache (instant)")
                        
                else:
                    st.error(f"Error: {response.text[:300]}")
                    
            except httpx.ConnectError:
                st.error("Cannot connect to the API. Make sure the backend is running.")
            except Exception as e:
                st.error(f"Error: {e}")


# ── Footer ──
st.markdown("""
<div class="footer">
    <strong>CodeSentinel AI</strong> v1.0.0<br/>
    <span class="tech-badge">FastAPI</span>
    <span class="tech-badge">Groq (Llama 3.3 70B)</span>
    <span class="tech-badge">Qdrant Vector DB</span>
    <span class="tech-badge">Redis Cache</span>
    <span class="tech-badge">Sentence Transformers</span>
    <span class="tech-badge">Docker</span>
</div>
""", unsafe_allow_html=True)
