from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DatasetVersion, Experiment, ModelConfig
from app.db.session import get_db
from app.schemas import ExperimentCreate, ExperimentRead, RunRead
from app.services.execution import execute_experiment

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=list[ExperimentRead])
def list_experiments(db: Session = Depends(get_db)) -> list[Experiment]:
    return list(db.scalars(select(Experiment).order_by(Experiment.created_at.desc())))


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)) -> Experiment:
    if db.get(DatasetVersion, payload.dataset_version_id) is None:
        raise HTTPException(status_code=404, detail="Dataset version not found.")
    model_config = db.get(ModelConfig, payload.model_config_id)
    if model_config is None or not model_config.is_enabled:
        raise HTTPException(status_code=404, detail="Enabled model configuration not found.")

    experiment = Experiment(**payload.model_dump())
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.get("/{experiment_id}", response_model=ExperimentRead)
def get_experiment(experiment_id: UUID, db: Session = Depends(get_db)) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    return experiment


@router.post("/{experiment_id}/runs", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def start_experiment_run(experiment_id: UUID, db: Session = Depends(get_db)):
    try:
        run = execute_experiment(db, experiment_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return run
