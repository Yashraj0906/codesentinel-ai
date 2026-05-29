# ============================================================
# evaluation/benchmark.py -- Run evaluation on test cases
# ============================================================
# RUN: python -m src.evaluation.benchmark
#
# This runs the bug detector on 10 test cases with known bugs,
# then calculates precision, recall, and F1 score.
# ============================================================

from src.review.diff_analyzer import DiffAnalyzer
from src.review.bug_detector import BugDetector
from src.evaluation.metrics import calculate_metrics, EvalResult


# Each test case: code + expected bugs
TEST_CASES = [
    {
        "name": "SQL Injection via f-string",
        "code": '''def get_user(id):\n    query = f"SELECT * FROM users WHERE id = {id}"\n    return db.execute(query)''',
        "expected_bugs": ["sql_injection"],
    },
    {
        "name": "Hardcoded password",
        "code": '''def connect():\n    password = "admin123"\n    return db.connect(password=password)''',
        "expected_bugs": ["hardcoded_secret"],
    },
    {
        "name": "Bare except with pass",
        "code": '''def process():\n    try:\n        do_work()\n    except:\n        pass''',
        "expected_bugs": ["bare_except", "swallowed_exception"],
    },
    {
        "name": "eval() on user input",
        "code": '''def calculate(expr):\n    return eval(expr)''',
        "expected_bugs": ["code_injection"],
    },
    {
        "name": "os.system with user input",
        "code": '''import os\ndef ping(host):\n    os.system(f"ping {host}")''',
        "expected_bugs": ["command_injection"],
    },
    {
        "name": "File opened without context manager",
        "code": '''def read_file(path):\n    f = open(path)\n    data = f.read()\n    return data''',
        "expected_bugs": ["resource_leak"],
    },
    {
        "name": "Mutable default argument",
        "code": '''def add_item(item, items=[]):\n    items.append(item)\n    return items''',
        "expected_bugs": ["mutable_default_argument"],
    },
    {
        "name": "Clean code -- no bugs",
        "code": '''def add(a: int, b: int) -> int:\n    return a + b''',
        "expected_bugs": [],
    },
    {
        "name": "Multiple vulnerabilities",
        "code": '''def login(user):\n    query = f"SELECT * FROM users WHERE name = '{user}'"\n    token = "sk-secret-key-123"\n    try:\n        result = eval(user)\n    except:\n        pass\n    return result''',
        "expected_bugs": ["sql_injection", "hardcoded_secret", "code_injection", "bare_except", "swallowed_exception"],
    },
    {
        "name": "Pickle deserialization",
        "code": '''import pickle\ndef load_data(data):\n    return pickle.loads(data)''',
        "expected_bugs": ["insecure_deserialization"],
    },
]


def run_benchmark():
    """Run all test cases and calculate metrics."""
    analyzer = DiffAnalyzer()
    detector = BugDetector()
    
    all_predicted = []
    all_expected = []
    results = []
    
    print("=" * 60)
    print("CODESENTINEL AI -- BENCHMARK")
    print("=" * 60)
    
    for i, tc in enumerate(TEST_CASES):
        print(f"\n[{i+1}/{len(TEST_CASES)}] {tc['name']}")
        
        # Run detection (static only -- skip LLM for speed)
        analysis = analyzer.parse_code(tc["code"])
        
        # Collect static pattern bugs only
        bugs = []
        for func in analysis.functions_changed:
            bugs.extend(detector._check_sql_injection(func))
            bugs.extend(detector._check_mutable_default(func))
            bugs.extend(detector._check_bare_except(func))
            bugs.extend(detector._check_hardcoded_secrets(func))
            bugs.extend(detector._check_resource_leak(func))
            bugs.extend(detector._check_dangerous_functions(func))
        
        predicted = list(set(b.bug_type for b in bugs))
        expected = tc["expected_bugs"]
        
        # Check results
        found = set(predicted) & set(expected)
        missed = set(expected) - set(predicted)
        extra = set(predicted) - set(expected)
        
        status = "PASS" if not missed else "PARTIAL" if found else "FAIL"
        print(f"   Expected: {expected}")
        print(f"   Found:    {predicted}")
        print(f"   Status:   {status}")
        if missed:
            print(f"   Missed:   {list(missed)}")
        
        all_predicted.extend(predicted)
        all_expected.extend(expected)
        
        results.append({
            "name": tc["name"],
            "status": status,
            "expected": expected,
            "predicted": predicted,
        })
    
    # Calculate overall metrics
    metrics = calculate_metrics(all_predicted, all_expected)
    
    print("\n" + "=" * 60)
    print("OVERALL RESULTS (Static Patterns Only)")
    print("=" * 60)
    print(f"  True Positives:  {metrics.true_positives}")
    print(f"  False Positives: {metrics.false_positives}")
    print(f"  False Negatives: {metrics.false_negatives}")
    print(f"  Precision:       {metrics.precision:.1%}")
    print(f"  Recall:          {metrics.recall:.1%}")
    print(f"  F1 Score:        {metrics.f1_score:.1%}")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"\n  {passed}/{len(results)} test cases fully passed")
    
    return metrics


if __name__ == "__main__":
    run_benchmark()
