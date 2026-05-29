# ============================================================
# evaluation/metrics.py -- Evaluation metrics
# ============================================================
# WHY THIS EXISTS:
# When you say "my tool finds bugs", interviewers ask:
#   "How well? What's the precision? What's the recall?"
#
# This file calculates those numbers so you can say:
#   "Precision: 85% (few false positives)"
#   "Recall: 78% (catches most real bugs)"
# ============================================================

from dataclasses import dataclass


@dataclass
class EvalResult:
    """Result of evaluating the bug detector on test cases."""
    true_positives: int     # Bugs correctly found
    false_positives: int    # Non-bugs flagged as bugs
    false_negatives: int    # Real bugs missed
    precision: float        # TP / (TP + FP) -- "how accurate are the findings?"
    recall: float           # TP / (TP + FN) -- "how many bugs did we catch?"
    f1_score: float         # Harmonic mean of precision and recall


def calculate_metrics(
    predicted_bugs: list[str],
    actual_bugs: list[str],
) -> EvalResult:
    """
    Compare predicted bugs against ground truth.
    
    Parameters:
        predicted_bugs: bug types found by the detector
        actual_bugs: bug types that actually exist (ground truth)
    
    Returns:
        EvalResult with precision, recall, and F1
    """
    predicted_set = set(predicted_bugs)
    actual_set = set(actual_bugs)
    
    tp = len(predicted_set & actual_set)      # Correctly found
    fp = len(predicted_set - actual_set)      # Falsely flagged
    fn = len(actual_set - predicted_set)      # Missed
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return EvalResult(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        precision=round(precision, 3),
        recall=round(recall, 3),
        f1_score=round(f1, 3),
    )
