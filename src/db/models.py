from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models. SQLAlchemy requirement."""
    pass


class User(Base):
    """
    Users table.
    Stores registered users who can submit code reviews.
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)            # UUID
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)    # Never store plain passwords!
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship: one user -> many reviews
    reviews = relationship("Review", back_populates="user")


class Review(Base):
    """
    Reviews table.
    Stores the results of each code review.
    """
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True)             # review ID (rev_20260529_...)
    user_id = Column(String, ForeignKey("users.id"))  # Who submitted it
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Input
    code_submitted = Column(Text)                     # The code that was reviewed
    file_path = Column(String, default="submitted_code.py")
    
    # Results
    risk_level = Column(String)                       # "low" | "medium" | "high"
    total_issues = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    issues_auto_fixed = Column(Integer, default=0)
    
    # Costs
    total_time_ms = Column(Integer)
    total_cost_usd = Column(Float)
    
    # Full report as JSON
    report_json = Column(JSON)
    
    # Relationship
    user = relationship("User", back_populates="reviews")


class ChatHistory(Base):
    """
    Chat history for the onboarding QA agent.
    Stores questions and answers about indexed codebases.
    """
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"))
    repo_url = Column(String)                         # Which repo was indexed
    question = Column(Text)
    answer = Column(Text)
    code_references = Column(JSON)                    # List of file/line references
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
