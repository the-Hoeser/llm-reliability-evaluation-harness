import json
from collections import Counter
from datetime import datetime, timezone
from statistics import mean
from time import perf_counter
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    DatasetVersion,
    EvaluationRun,
    ExecutionEvent,
    Experiment,
    ModelConfig,
    TestCase,
    TestResult,
)
from app.services.evaluator import evaluate_output
from app.services.model_adapter import ModelAdapterError, build_model_adapter


MAX_CASES_PER_RUN = 100


def _event(
    db: Session,
    *,
    run_id: UUID,
    event_type: str,
    message: str,
    level: str = "info",
    test_result_id: UUID | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(
        ExecutionEvent(
            run_id=run_id,
            test_result_id=test_result_id,
            level=level,
            event_type=event_type,
            message=message,
            details=details or {},
        )
    )


def _format_case_input(case: TestCase) -> str:
    if case.context is None:
        return case.input_text
    if isinstance(case.context, str):
        context_text = case.context
    else:
        context_text = json.dumps(case.context, ensure_ascii=False, sort_keys=True)
    return f"Context:\n{context_text}\n\nQuestion:\n{case.input_text}"


def execute_experiment(db: Session, experiment_id: UUID) -> EvaluationRun:
    """Execute an experiment sequentially on the local API process and persist every case."""
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise ValueError("Experiment not found.")

    model_config = db.get(ModelConfig, experiment.model_config_id)
    dataset_version = db.get(DatasetVersion, experiment.dataset_version_id)
    if model_config is None or not model_config.is_enabled:
        raise ValueError("The experiment model configuration is missing or disabled.")
    if dataset_version is None:
        raise ValueError("The experiment dataset version does not exist.")

    test_cases = list(
        db.scalars(
            select(TestCase)
            .where(TestCase.dataset_version_id == dataset_version.id)
            .order_by(TestCase.external_id)
            .limit(MAX_CASES_PER_RUN + 1)
        )
    )
    if not test_cases:
        raise ValueError("The selected dataset version contains no test cases.")
    if len(test_cases) > MAX_CASES_PER_RUN:
        raise ValueError(f"A local run is limited to {MAX_CASES_PER_RUN} test cases.")

    adapter = build_model_adapter(model_config)
    model_snapshot = {
        "provider": model_config.provider,
        "model_id": model_config.model_id,
        "endpoint_url": model_config.endpoint_url,
        "parameters": model_config.parameters,
    }
    evaluator_snapshot = dict(experiment.evaluator_config)

    run = EvaluationRun(
        id=uuid4(),
        experiment_id=experiment.id,
        status="running",
        system_prompt_snapshot=experiment.system_prompt,
        model_config_snapshot=model_snapshot,
        evaluator_config_snapshot=evaluator_snapshot,
        summary={},
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()
    _event(db, run_id=run.id, event_type="run.started", message="Evaluation run started.")
    db.commit()

    scores: list[float] = []
    failure_categories: Counter[str] = Counter()
    succeeded = 0
    errors = 0

    try:
        for case in test_cases:
            started = perf_counter()
            try:
                response = adapter.generate(
                    input_text=_format_case_input(case),
                    system_prompt=experiment.system_prompt,
                    parameters=model_config.parameters,
                )
                latency_ms = round((perf_counter() - started) * 1000)
                evaluation = evaluate_output(case.expected_output, response.output_text)
                result = TestResult(
                    run_id=run.id,
                    test_case_id=case.id,
                    status="succeeded",
                    model_output=response.output_text,
                    score=evaluation["score"],
                    failure_category=evaluation["failure_category"],
                    metrics=evaluation["metrics"],
                    latency_ms=latency_ms,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                )
                db.add(result)
                db.flush()
                succeeded += 1
                if result.score is not None:
                    scores.append(result.score)
                if result.failure_category:
                    failure_categories[result.failure_category] += 1
                _event(
                    db,
                    run_id=run.id,
                    test_result_id=result.id,
                    event_type="test_case.succeeded",
                    message=f"Test case {case.external_id} completed.",
                    details={"latency_ms": latency_ms, "score": result.score},
                )
            except ModelAdapterError as exc:
                errors += 1
                latency_ms = round((perf_counter() - started) * 1000)
                failure_categories["provider_error"] += 1
                result = TestResult(
                    run_id=run.id,
                    test_case_id=case.id,
                    status="error",
                    model_output=None,
                    score=None,
                    failure_category="provider_error",
                    metrics={"scoring_method": "not_run"},
                    latency_ms=latency_ms,
                    error_message=str(exc),
                )
                db.add(result)
                db.flush()
                _event(
                    db,
                    run_id=run.id,
                    test_result_id=result.id,
                    event_type="test_case.failed",
                    level="error",
                    message=f"Test case {case.external_id} failed at the provider boundary.",
                    details={"latency_ms": latency_ms, "error": str(exc)},
                )
            db.commit()

        summary = {
            "total_cases": len(test_cases),
            "succeeded": succeeded,
            "errors": errors,
            "scored": len(scores),
            "unscored": succeeded - len(scores),
            "mean_score": round(mean(scores), 4) if scores else None,
            "failure_categories": dict(failure_categories),
        }
        run.status = (
            "completed_with_errors" if errors and succeeded
            else ("failed" if errors else "completed")
        )
        run.summary = summary
        run.completed_at = datetime.now(timezone.utc)
        _event(
            db,
            run_id=run.id,
            event_type="run.completed",
            message="Evaluation run finished.",
            details=summary,
        )
        db.commit()
        db.refresh(run)
        return run
    except Exception:
        db.rollback()
        current_run = db.get(EvaluationRun, run.id)
        if current_run is not None:
            current_run.status = "failed"
            current_run.completed_at = datetime.now(timezone.utc)
            current_run.summary = {
                "total_cases": len(test_cases),
                "succeeded": succeeded,
                "errors": errors,
            }
            _event(
                db,
                run_id=current_run.id,
                event_type="run.failed",
                level="error",
                message="Evaluation run failed unexpectedly.",
            )
            db.commit()
        raise
