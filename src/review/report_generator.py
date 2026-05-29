# ============================================================
# report_generator.py — Builds the final review report
# ============================================================
# Takes all results (bugs, fixes, test results, costs) and
# produces a structured report in JSON and Markdown format.
# ============================================================

from dataclasses import dataclass
from datetime import datetime
from src.review.diff_analyzer import DiffAnalysis
from src.review.bug_detector import BugReport
from src.review.fix_generator import CodeFix
from src.review.test_runner import SelfHealResult
from src.shared.cost_tracker import CostTracker


@dataclass
class ReviewReport:
    """Complete code review report."""
    review_id: str
    timestamp: str
    files_changed: list[str]
    risk_level: str
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    issues_auto_fixed: int
    self_heal_attempts: int
    total_time_ms: int
    total_cost_usd: float
    issues: list[dict]
    summary: str


class ReportGenerator:
    """Generates structured review reports."""
    
    def generate(
        self,
        analysis: DiffAnalysis,
        bugs: list[BugReport],
        fixes: list[CodeFix],
        heal_results: list[SelfHealResult],
        cost_tracker: CostTracker,
        total_time_ms: int,
    ) -> ReviewReport:
        """Build the complete review report from all pipeline results."""
        
        # Count by severity
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for bug in bugs:
            counts[bug.severity] = counts.get(bug.severity, 0) + 1
        
        # Count auto-fixed
        auto_fixed = sum(1 for r in heal_results if r.success)
        total_heal = sum(r.attempts for r in heal_results)
        
        # Build detailed issues list
        issues = []
        for i, bug in enumerate(bugs):
            issue = {
                "bug_type": bug.bug_type,
                "severity": bug.severity,
                "file_path": bug.file_path,
                "line_number": bug.line_number,
                "description": bug.description,
                "suggestion": bug.suggestion,
                "confidence": bug.confidence,
                "detection_method": bug.detection_method,
                "auto_fixed": heal_results[i].success if i < len(heal_results) else False,
            }
            if i < len(fixes) and fixes[i].fixed_code:
                issue["fix"] = {
                    "original_code": fixes[i].original_code[:300],
                    "fixed_code": fixes[i].fixed_code[:300],
                    "explanation": fixes[i].explanation,
                }
            issues.append(issue)
        
        summary = self._make_summary(len(bugs), counts, auto_fixed)
        
        return ReviewReport(
            review_id=f"rev_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            files_changed=analysis.files_changed,
            risk_level=analysis.risk_level,
            total_issues=len(bugs),
            critical_count=counts["critical"],
            high_count=counts["high"],
            medium_count=counts["medium"],
            low_count=counts["low"],
            issues_auto_fixed=auto_fixed,
            self_heal_attempts=total_heal,
            total_time_ms=total_time_ms,
            total_cost_usd=cost_tracker.total_cost,
            issues=issues,
            summary=summary,
        )
    
    def _make_summary(self, total: int, counts: dict, fixed: int) -> str:
        if total == 0:
            return "No issues found. Code looks clean!"
        parts = [f"Found {total} issue(s):"]
        if counts["critical"]: parts.append(f"[CRITICAL] {counts['critical']} critical")
        if counts["high"]: parts.append(f"[HIGH] {counts['high']} high")
        if counts["medium"]: parts.append(f"[MEDIUM] {counts['medium']} medium")
        if counts["low"]: parts.append(f"[LOW] {counts['low']} low")
        parts.append(f"| Auto-fixed: {fixed}/{total}")
        return " ".join(parts)
    
    def to_markdown(self, report: ReviewReport) -> str:
        """Render report as Markdown for Streamlit display."""
        risk_icon = {"high": "[!!!]", "medium": "[!!]", "low": "[!]"}.get(report.risk_level, "[-]")
        
        md = f"""# Code Review Report

**ID:** {report.review_id} | **Risk:** {risk_icon} {report.risk_level.upper()}

## Summary
{report.summary}

| Metric | Value |
|--------|-------|
| Files Changed | {len(report.files_changed)} |
| Total Issues | {report.total_issues} |
| Auto-Fixed | {report.issues_auto_fixed} |
| Self-Heal Attempts | {report.self_heal_attempts} |
| Review Time | {report.total_time_ms}ms |
| LLM Cost | ${report.total_cost_usd:.4f} |

## Issues
"""
        for issue in report.issues:
            icon = {"critical": "[CRITICAL]", "high": "[HIGH]", "medium": "[MEDIUM]", "low": "[LOW]"}.get(issue["severity"], "[-]")
            status = "[FIXED]" if issue.get("auto_fixed") else "[NEEDS REVIEW]"
            
            md += f"""
### {icon} {issue['bug_type'].replace('_', ' ').title()}
- **Severity:** {issue['severity']} | **Status:** {status}
- **File:** `{issue['file_path']}` line {issue.get('line_number', '?')}
- **Description:** {issue['description']}
- **Fix:** {issue['suggestion']}
"""
        return md
