from src.shared.vector_store import VectorStore
from src.config import get_settings


# Each entry is ONE known vulnerability type.
# The "text" field contains: description + vulnerable code patterns + fixes
# This is what gets embedded and searched against.
CWE_DATA = [
    {
        "id": "cwe_89",
        "text": """CWE-89: SQL Injection. The software constructs SQL commands using 
        user input without proper sanitization.
        
        Vulnerable patterns:
        - f"SELECT * FROM users WHERE name = '{user_input}'"
        - "SELECT * FROM users WHERE name = '" + user_input + "'"
        - cursor.execute("SELECT * FROM users WHERE id = %d" % user_id)
        
        Fix: Use parameterized queries:
        - cursor.execute("SELECT * FROM users WHERE name = %s", (user_input,))
        - Use ORM: User.query.filter_by(name=user_input)""",
        "metadata": {"cwe_id": "CWE-89", "category": "injection", "severity": "critical"}
    },
    {
        "id": "cwe_79",
        "text": """CWE-79: Cross-site Scripting (XSS). User input is placed directly 
        into HTML output without escaping.
        
        Vulnerable patterns:
        - return f"<h1>Welcome {username}</h1>"
        - response.write("<div>" + user_comment + "</div>")
        - template with |safe filter on user input
        
        Fix: Always escape user input:
        - Use html.escape(user_input)
        - Use template engine's auto-escaping
        - Set Content-Security-Policy headers""",
        "metadata": {"cwe_id": "CWE-79", "category": "injection", "severity": "high"}
    },
    {
        "id": "cwe_78",
        "text": """CWE-78: OS Command Injection. User input is passed to system 
        commands without sanitization.
        
        Vulnerable patterns:
        - os.system(f"ping {user_host}")
        - subprocess.call(f"ls {directory}", shell=True)
        - os.popen("cat " + filename)
        
        Fix: 
        - Use subprocess with list args: subprocess.run(["ping", host])
        - Never use shell=True with user input
        - Use shlex.quote() to escape arguments""",
        "metadata": {"cwe_id": "CWE-78", "category": "injection", "severity": "critical"}
    },
    {
        "id": "cwe_22",
        "text": """CWE-22: Path Traversal. User input is used in file paths without 
        validation, allowing access to unauthorized files.
        
        Vulnerable patterns:
        - open(f"/uploads/{user_filename}")
        - os.path.join(base_dir, user_input)
        - shutil.copy(user_path, destination)
        
        Fix:
        - Use os.path.realpath() and verify it starts with allowed directory
        - Use pathlib and resolve() to normalize paths
        - Reject inputs containing .. or absolute paths""",
        "metadata": {"cwe_id": "CWE-22", "category": "file_access", "severity": "high"}
    },
    {
        "id": "cwe_798",
        "text": """CWE-798: Hardcoded Credentials. Passwords, API keys, or tokens 
        are embedded directly in source code.
        
        Vulnerable patterns:
        - password = "admin123"
        - API_KEY = "sk-1234567890"
        - connection_string = "postgresql://user:realpass@host/db"
        
        Fix:
        - Use environment variables: os.environ.get('API_KEY')
        - Use .env files with python-dotenv
        - Use a secrets manager""",
        "metadata": {"cwe_id": "CWE-798", "category": "credentials", "severity": "critical"}
    },
    {
        "id": "cwe_502",
        "text": """CWE-502: Deserialization of Untrusted Data. Deserializing data 
        from untrusted sources can execute arbitrary code.
        
        Vulnerable patterns:
        - pickle.loads(user_data)
        - yaml.load(user_input) without Loader parameter
        - marshal.loads(untrusted_bytes)
        
        Fix:
        - Never pickle untrusted data
        - Use yaml.safe_load() instead of yaml.load()
        - Use json for data exchange""",
        "metadata": {"cwe_id": "CWE-502", "category": "deserialization", "severity": "critical"}
    },
    {
        "id": "cwe_20",
        "text": """CWE-20: Improper Input Validation. User input is used without 
        checking type, length, range, or format.
        
        Vulnerable patterns:
        - Using user input directly without type checking
        - No length limits on string inputs
        - No range validation on numeric inputs
        - No format validation on emails, URLs
        
        Fix:
        - Validate type, length, range, and format of all inputs
        - Use Pydantic models for automatic validation
        - Whitelist allowed values when possible""",
        "metadata": {"cwe_id": "CWE-20", "category": "validation", "severity": "high"}
    },
    {
        "id": "cwe_287",
        "text": """CWE-287: Improper Authentication. The system does not properly 
        verify that a user is who they claim to be.
        
        Vulnerable patterns:
        - Checking username but not password
        - Using == instead of constant-time comparison for tokens
        - No rate limiting on login attempts
        - Session tokens that are predictable
        
        Fix:
        - Use bcrypt/argon2 for password hashing
        - Use hmac.compare_digest() for token comparison
        - Implement rate limiting and account lockout""",
        "metadata": {"cwe_id": "CWE-287", "category": "authentication", "severity": "critical"}
    },
    {
        "id": "cwe_862",
        "text": """CWE-862: Missing Authorization. The system does not check if a 
        user has permission to perform an action.
        
        Vulnerable patterns:
        - API endpoints with no auth check
        - def delete_user(user_id): without verifying caller's role
        - Direct object reference without ownership check
        
        Fix:
        - Check permissions on every endpoint
        - Use role-based access control (RBAC)
        - Verify resource ownership before operations""",
        "metadata": {"cwe_id": "CWE-862", "category": "authorization", "severity": "critical"}
    },
    {
        "id": "cwe_918",
        "text": """CWE-918: Server-Side Request Forgery (SSRF). The server makes 
        HTTP requests to URLs controlled by the user.
        
        Vulnerable patterns:
        - requests.get(user_provided_url)
        - urllib.urlopen(url_from_input)
        - Fetching images/files from user-supplied URLs
        
        Fix:
        - Whitelist allowed domains
        - Block internal/private IP ranges
        - Use URL validation before making requests""",
        "metadata": {"cwe_id": "CWE-918", "category": "ssrf", "severity": "high"}
    },
]


def seed():
    """Seed CWE data into Qdrant vector database."""
    settings = get_settings()
    vs = VectorStore()
    
    vs.create_collection(settings.qdrant_collection_cve, dimension=settings.embedding_dimension)
    
    # Insert all CWE entries
    vs.upsert(settings.qdrant_collection_cve, CWE_DATA)
    
    print(f"\n[OK] Seeded {len(CWE_DATA)} CWE entries into Qdrant")
    print(f"   Collection: {settings.qdrant_collection_cve}")
    print(f"   You can now use the security scanner!")


if __name__ == "__main__":
    seed()
