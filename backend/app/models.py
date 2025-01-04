from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Experiment(Base):
    __tablename__ = 'experiments'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    system_prompt = Column(Text)
    llm_model = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

class TestCase(Base):
    __tablename__ = 'test_cases'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    user_message = Column(Text)
    expected_output = Column(Text)
    grader_type = Column(String)  # e.g., exact_match, partial_match
    created_at = Column(DateTime, default=datetime.utcnow)

class ExperimentRun(Base):
    __tablename__ = 'experiment_runs'
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id'))
    run_timestamp = Column(DateTime, default=datetime.utcnow)

class RunResult(Base):
    __tablename__ = 'run_results'
    id = Column(Integer, primary_key=True, index=True)
    experiment_run_id = Column(Integer, ForeignKey('experiment_runs.id'))
    test_case_id = Column(Integer, ForeignKey('test_cases.id'))
    actual_output = Column(Text)
    score = Column(Float)
