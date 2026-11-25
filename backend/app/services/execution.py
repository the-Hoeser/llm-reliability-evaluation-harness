import json
from collections import Counter
from datetime import UTC, datetime
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
from app.services.uncertainty import (
    UncertaintyResponseError,
    evaluate_uncertainty_case,
    summarize_uncertainty_cases,
    validate_uncertainty_dataset_case,
)


MAX_CASES_PER_RUN = 100
UNCERTAINTY_METHODS = {"forced_answer_v1", "abstention_calibration_v1"}


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


def _build_system_prompt(base_prompt: str | None, method: str) -> str | None:
    if method not in UNCERTAINTY_METHODS:
        return base_prompt

    common = (
        "This is a closed-context question-answering evaluation. Use only the supplied context. "
        "Do not use outside knowledge. Treat missing or ambiguous evidence as insufficient support. "
    )
    if method == "forced_answer_v1":
        instruction = (
            common
            + "You are in the forced-answer baseline condition: always provide your best answer, "
            "even when the context does not support it. Do not abstain. Return only a valid JSON "
            'object with exactly these fields: {"answer": "string", "confidence": 0.0}. '
            "Confidence is your probability, from 0 to 1, that the proposed answer is correct "
            "and supported by the supplied context."
        )
    else:
        instruction = (
            common
            + "You are in the selective-answering condition. If the context clearly supports an "
            "answer, provide it. If the answer is absent or the question is underspecified, abstain. "
            "When abstaining, set answer to null and abstained to true. When answering, provide a "
            "string answer and set abstained to false. Return only a valid JSON object with exactly "
            'these fields: {"answer": "string or null", "confidence": 0.0, "abstained": false}. '
            "Confidence is your probability, from 0 to 1, that a proposed answer is correct and "
            "supported by the supplied context. Do not reveal private chain-of-thought."
        )
    return f"{base_prompt.strip()}\n\n{instruction}" if base_prompt else instruction


def _validate_uncertainty_cases(test_cases: list[TestCase]) -> None:
    for case in test_cases:
        try:
            validate_uncertainty_dataset_case(case.expected_output, case.context)
        except ValueError as exc:
            raise ValueError(
                f"Test case '{case.external_id}' is invalid for the uncertainty evaluator: {exc}"
            ) from exc


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

    evaluator_method = experiment.evaluator_config.get("method", "normalized_exact_match")
    is_uncertainty_run = evaluator_method in UNCERTAINTY_METHODS
    if is_uncertainty_run:
        _validate_uncertainty_cases(test_cases)

    adapter = build_model_adapter(model_config)
    effective_system_prompt = _build_system_prompt(experiment.system_prompt, evaluator_method)
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
        system_prompt_snapshot=effective_system_prompt,
        model_config_snapshot=model_snapshot,
        evaluator_config_snapshot=evaluator_snapshot,
        summary={},
        started_at=datetime.now(UTC),
    )
    db.add(run)
    db.flush()
    _event(db, run_id=run.id, event_type="run.started", message="Evaluation run started.")
    db.commit()

    scores: list[float] = []
    uncertainty_metrics: list[dict[str, Any]] = []
    failure_categories: Counter[str] = Counter()
    succeeded = 0
    errors = 0

    try:
        for case in test_cases:
            started = perf_counter()
            try:
                response = adapter.generate(
                    input_text=_format_case_input(case),
                    system_prompt=effective_system_prompt,
                    parameters=model_config.parameters,
                    json_mode=is_uncertainty_run,
                )
                latency_ms = round((perf_counter() - started) * 1000)

                if is_uncertainty_run:
                    try:
                        evaluation = evaluate_uncertainty_case(
                            case.expected_output,
                            response.output_text,
                            evaluator_method,
                        )
                        case_metric = {
                            **evaluation["metrics"],
                            "answerability": case.expected_output["answerability"],
                            "confidence": evaluation["confidence"],
                            "abstained": evaluation["abstained"],
                            "failure_category": evaluation["failure_category"],
                            "response_valid": True,
                        }
                    except UncertaintyResponseError as exc:
                        evaluation = {
                            "score": 0.0,
                            "confidence": None,
                            "abstained": None,
                            "failure_category": "invalid_response_format",
                            "metrics": {
                                "scoring_method": evaluator_method,
                                "answerability": case.expected_output["answerability"],
                                "response_valid": False,
                                "parse_error": str(exc),
                            },
                        }
                        case_metric = {
                            **evaluation["metrics"],
                            "answerability": case.expected_output["answerability"],
                            "confidence": None,
                            "abstained": None,
                            "failure_category": "invalid_response_format",
                            "response_valid": False,
                        }
                    uncertainty_metrics.append(case_metric)
                else:
                    evaluation = evaluate_output(case.expected_output, response.output_text)

                result = TestResult(
                    run_id=run.id,
                    test_case_id=case.id,
                    status="succeeded",
                    model_output=response.output_text,
                    score=evaluation["score"],
                    confidence=evaluation.get("confidence"),
                    abstained=evaluation.get("abstained"),
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
                    details={
                        "latency_ms": latency_ms,
                        "score": result.score,
                        "confidence": result.confidence,
                        "abstained": result.abstained,
                        "failure_category": result.failure_category,
                    },
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
                    confidence=None,
                    abstained=None,
                    failure_category="provider_error",
                    metrics={"scoring_method": evaluator_method, "response_valid": False},
                    latency_ms=latency_ms,
                    error_message=str(exc),
                )
                db.add(result)
                db.flush()
                if is_uncertainty_run:
                    uncertainty_metrics.append({
                        "answerability": case.expected_output["answerability"],
                        "response_valid": False,
                        "abstained": None,
                        "confidence": None,
                        "failure_category": "provider_error",
                    })
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

        if is_uncertainty_run:
            summary = summarize_uncertainty_cases(uncertainty_metrics, evaluator_method)
            summary["succeeded"] = succeeded
            summary["errors"] = errors
            summary["scored"] = len(scores)
            summary["mean_decision_score"] = round(mean(scores), 4) if scores else None
        else:
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
        run.completed_at = datetime.now(UTC)
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
            current_run.completed_at = datetime.now(UTC)
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
