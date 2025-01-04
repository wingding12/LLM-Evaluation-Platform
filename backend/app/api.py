from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Experiment, TestCase, ExperimentRun, RunResult
from pydantic import BaseModel
from app.tasks import run_experiment_task

app = FastAPI()

class ExperimentCreate(BaseModel):
    name: str
    system_prompt: str
    llm_model: str

@app.post("/experiments/")
def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    new_experiment = Experiment(
        name=experiment.name,
        system_prompt=experiment.system_prompt,
        llm_model=experiment.llm_model
    )
    db.add(new_experiment)
    db.commit()
    db.refresh(new_experiment)
    return new_experiment

@app.post("/experiments/{experiment_id}/run")
def run_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    task_id = run_experiment_task.delay(experiment_id)
    return {"task_id": task_id}
