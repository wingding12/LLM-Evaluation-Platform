from celery import Celery
from .database import SessionLocal
from .models import Experiment, TestCase, RunResult, ExperimentTestCases
from difflib import SequenceMatcher
import re
import asyncio
from .services.llm_service import LLMService, LLMProvider

celery = Celery(__name__, broker="redis://localhost:6379/0")

llm_service = LLMService()

def call_llm_api(system_prompt: str, user_message: str, model: str = "gpt-3.5-turbo") -> str:
    return asyncio.run(llm_service.generate_response(model, system_prompt, user_message))

def grade_output(expected: str, actual: str, grader_type: str) -> float:
    if grader_type == "exact_match":
        return 1.0 if expected.strip() == actual.strip() else 0.0
    
    elif grader_type == "similarity":
        # Use sequence matcher for fuzzy string matching
        return SequenceMatcher(None, expected.lower(), actual.lower()).ratio()
    
    elif grader_type == "contains_key_elements":
        # Check if all key elements from expected are in actual
        expected_elements = set(re.findall(r'\w+', expected.lower()))
        actual_elements = set(re.findall(r'\w+', actual.lower()))
        if not expected_elements:
            return 0.0
        return len(expected_elements.intersection(actual_elements)) / len(expected_elements)
    
    elif grader_type == "json_match":
        try:
            import json
            expected_json = json.loads(expected)
            actual_json = json.loads(actual)
            return 1.0 if expected_json == actual_json else 0.0
        except json.JSONDecodeError:
            return 0.0
    
    return 0.0  # Default case for unknown grader_type

@celery.task
def run_experiment_task(experiment_id):
    db = SessionLocal()
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    test_cases = db.query(TestCase).join(ExperimentTestCases).filter(ExperimentTestCases.experiment_id == experiment_id).all()
    
    for test_case in test_cases:
        actual_output = call_llm_api(
            experiment.system_prompt, 
            test_case.user_message,
            experiment.llm_model
        )
        score = grade_output(test_case.expected_output, actual_output, test_case.grader_type)
        
        result = RunResult(
            experiment_id=experiment_id,
            test_case_id=test_case.id,
            actual_output=actual_output,
            score=score
        )
        db.add(result)
    db.commit()
