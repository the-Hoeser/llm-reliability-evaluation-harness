from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EvaluationRun, TestCase, TestResult
from app.db.session import get_db
from app.schemas import RunDetail, TestResultRead

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: UUID, db: Session = Depends(get_db)) -> RunDetail:
    run = db.get(EvaluationRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")

    results = list(
        db.scalars(
            select(TestResult)
            .join(TestCase, TestCase.id == TestResult.test_case_id)
            .where(TestResult.run_id == run_id)
            .order_by(TestCase.external_id)
        )
    )
    return RunDetail(
        id=run.id,
        experiment_id=run.experiment_id,
        status=run.status,
        summary=run.summary,
        started_at=run.started_at,
        completed_at=run.completed_at,
        results=[TestResultRead.model_validate(item) for item in results],
    )


@router.get("/{run_id}/results", response_model=list[TestResultRead])
def list_run_results(run_id: UUID, db: Session = Depends(get_db)) -> list[TestResult]:
    if db.get(EvaluationRun, run_id) is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found.")
    return list(
        db.scalars(
            select(TestResult)
            .join(TestCase, TestCase.id == TestResult.test_case_id)
            .where(TestResult.run_id == run_id)
            .order_by(TestCase.external_id)
        )
    )
