import time
from src.review.diff_analyzer import DiffAnalyzer
from src.review.bug_detector import BugDetector
from src.review.security_scanner import SecurityScanner
from src.review.fix_generator import FixGenerator
from src.review.test_runner import TestRunner
from src.review.report_generator import ReportGenerator, ReviewReport
from src.shared.cost_tracker import CostTracker


class CodeReviewPipeline:
    """
    The full code review pipeline.
    
    FLOW:
    1. DiffAnalyzer  → parse code, extract functions
    2. BugDetector   → static patterns + LLM analysis
    3. SecurityScan  → RAG on CWE database
    4. FixGenerator  → generate code fixes
    5. TestRunner    → test fixes with self-healing
    6. ReportGen     → produce final report
    """
    
    def __init__(self):
        self.diff_analyzer = DiffAnalyzer()
        self.bug_detector = BugDetector()
        self.security_scanner = SecurityScanner()
        self.fix_generator = FixGenerator()
        self.test_runner = TestRunner()
        self.report_generator = ReportGenerator()
    
    def review_code(self, code: str, file_path: str = "submitted_code.py") -> ReviewReport:
        """
        Review a code string. This is the main method.
        """
        start_time = time.time()
        cost_tracker = CostTracker()
        
        print("[1/6] Analyzing code structure...")
        analysis = self.diff_analyzer.parse_code(code, file_path)
        print(f"   Found {len(analysis.functions_changed)} function(s), risk: {analysis.risk_level}")
        
        print("[2/6] Detecting bugs (static patterns)...")
        bugs = self.bug_detector.detect(analysis)
        print(f"   Found {len(bugs)} issue(s) from bug detector")
        
        print("[3/6] Security scan (RAG on CWE)...")
        try:
            security_issues = self.security_scanner.scan(analysis)
            print(f"   Found {len(security_issues)} security issue(s)")
        except Exception as e:
            print(f"   [WARN] Security scan skipped: {e}")
            security_issues = []
        
        all_bugs = bugs + security_issues
        
        print(f"[4/6] Generating fixes for {len(all_bugs)} issue(s)...")
        fixes = self.fix_generator.generate_fixes(all_bugs, code)
        
        print("[5/6] Testing fixes with self-healing...")
        heal_results = []
        for i, fix in enumerate(fixes):
            if fix.fixed_code:
                print(f"   Testing fix {i+1}/{len(fixes)}: {fix.bug.bug_type}")
                try:
                    result = self.test_runner.run_with_self_heal(fix, code)
                    heal_results.append(result)
                except Exception as e:
                    print(f"   [WARN] Self-heal failed for {fix.bug.bug_type}: {e}")
                    from src.review.test_runner import SelfHealResult
                    heal_results.append(SelfHealResult(
                        success=False, final_fix=fix, attempts=0,
                        test_results=[], heal_log=[f"Self-heal error: {e}"]
                    ))
            else:
                # No fix generated — create a dummy result
                from src.review.test_runner import SelfHealResult
                heal_results.append(SelfHealResult(
                    success=False, final_fix=None, attempts=0,
                    test_results=[], heal_log=["No fix generated"]
                ))
        
        print("[6/6] Generating report...")
        total_time = int((time.time() - start_time) * 1000)
        
        # Collect cost from all LLM clients
        cost_tracker = self.bug_detector.llm.cost_tracker
        
        report = self.report_generator.generate(
            analysis, all_bugs, fixes, heal_results, cost_tracker, total_time
        )
        
        print(f"\n{'='*50}")
        print(f"{report.summary}")
        print(f"Time: {report.total_time_ms}ms | Cost: ${report.total_cost_usd:.4f}")
        print(f"{'='*50}\n")
        
        return report
    
    def review_diff(self, diff_text: str) -> ReviewReport:
        """Review a git diff string."""
        start_time = time.time()
        cost_tracker = CostTracker()
        
        analysis = self.diff_analyzer.parse_diff(diff_text)
        bugs = self.bug_detector.detect(analysis)
        
        try:
            security_issues = self.security_scanner.scan(analysis)
        except Exception:
            security_issues = []
        
        all_bugs = bugs + security_issues
        fixes = self.fix_generator.generate_fixes(all_bugs, diff_text)
        
        heal_results = []
        for fix in fixes:
            if fix.fixed_code:
                try:
                    result = self.test_runner.run_with_self_heal(fix, diff_text)
                    heal_results.append(result)
                except Exception as e:
                    print(f"   [WARN] Self-heal failed: {e}")
                    from src.review.test_runner import SelfHealResult
                    heal_results.append(SelfHealResult(
                        success=False, final_fix=fix, attempts=0,
                        test_results=[], heal_log=[f"Self-heal error: {e}"]
                    ))
            else:
                from src.review.test_runner import SelfHealResult
                heal_results.append(SelfHealResult(
                    success=False, final_fix=None, attempts=0,
                    test_results=[], heal_log=["No fix generated"]
                ))
        
        total_time = int((time.time() - start_time) * 1000)
        cost_tracker = self.bug_detector.llm.cost_tracker
        
        return self.report_generator.generate(
            analysis, all_bugs, fixes, heal_results, cost_tracker, total_time
        )
