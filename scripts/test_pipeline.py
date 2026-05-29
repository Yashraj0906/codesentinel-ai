"""Quick test of the full code review pipeline."""
from src.review import CodeReviewPipeline
from src.review.report_generator import ReportGenerator

pipeline = CodeReviewPipeline()

bad_code = """
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    password = "admin123"
    try:
        result = eval(username)
    except:
        pass
    return result
"""

print("=" * 50)
print("TESTING CODE REVIEW PIPELINE")
print("=" * 50)

report = pipeline.review_code(bad_code)

print("\n" + "=" * 50)
print("FULL MARKDOWN REPORT:")
print("=" * 50)
print(ReportGenerator().to_markdown(report))
