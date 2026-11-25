from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DatasetVersion, Experiment, ModelConfig, TestCase
from app.db.session import get_db
from app.schemas import ExperimentCreate, ExperimentRead, RunRead
from app.services.execution import execute_experiment
from app.services.uncertainty import validate_uncertainty_dataset_case

router = APIRouter(prefix="/experiments", tags=["experiments"])
UNCERTAINTY_METHODS = {"forced_answer_v1", "abstention_calibration_v1"}


@router.get("", response_model=list[ExperimentRead])
def list_experiments(db: Session = Depends(get_db)) -> list[Experiment]:
    return list(db.scalars(select(Experiment).order_by(Experiment.created_at.desc())))


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db)) -> Experiment:
    dataset_version = db.get(DatasetVersion, payload.dataset_version_id)
    if dataset_version is None:
        raise HTTPException(status_code=404, detail="Dataset version not found.")
    model_config = db.get(ModelConfig, payload.model_config_id)
    if model_config is None or not model_config.is_enabled:
        raise HTTPException(status_code=404, detail="Enabled model configuration not found.")

    method = payload.evaluator_config.get("method", "normalized_exact_match")
    if method in UNCERTAINTY_METHODS:
        cases = list(
            db.scalars(
                select(TestCase)
                .where(TestCase.dataset_version_id == dataset_version.id)
                .order_by(TestCase.external_id)
            )
        )
        if not cases:
            raise HTTPException(status_code=422, detail="The selected dataset version is empty.")
        for case in cases:
            try:
                validate_uncertainty_dataset_case(case.expected_output, case.context)
            except ValueError as exc:
                raise HTTPException(
                    status_code=422,
                    detail=f"Test case '{case.external_id}' is not valid for {method}: {exc}",
                ) from exc

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
