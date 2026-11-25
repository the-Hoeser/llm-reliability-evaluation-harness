import json
import math
from collections import Counter
from statistics import mean
from typing import Any

ANSWERABILITY_LABELS = {"answerable", "unanswerable", "underspecified"}


class UncertaintyResponseError(ValueError):
    """The model did not satisfy the structured uncertainty response contract."""


def validate_uncertainty_dataset_case(expected_output: Any, context: Any) -> None:
    """Validate one closed-context test case before it enters an experiment."""
    if not isinstance(context, (str, dict, list)) or not context:
        raise ValueError("Every uncertainty test case must contain non-empty context.")
    if not isinstance(expected_output, dict):
        raise ValueError("Uncertainty test cases require an object expected_output.")

    answerability = expected_output.get("answerability")
    if answerability not in ANSWERABILITY_LABELS:
        raise ValueError(
            "expected_output.answerability must be answerable, unanswerable, or underspecified."
        )

    if answerability == "answerable":
        acceptable = expected_output.get("acceptable_answers")
        if (
            not isinstance(acceptable, list)
            or not acceptable
            or any(not isinstance(item, str) or not item.strip() for item in acceptable)
        ):
            raise ValueError(
                "Answerable cases require a non-empty acceptable_answers string list."
            )


def parse_uncertainty_response(raw_output: str, policy: str) -> dict[str, Any]:
    """Parse the public JSON response contract; never infer confidence from prose."""
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise UncertaintyResponseError("Model output was not valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise UncertaintyResponseError("Model output must be a JSON object.")

    answer = parsed.get("answer")
    confidence = parsed.get("confidence")
    if answer is not None and not isinstance(answer, str):
        raise UncertaintyResponseError("The answer field must be a string or null.")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise UncertaintyResponseError("The confidence field must be a number from 0 to 1.")

    confidence = float(confidence)
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise UncertaintyResponseError("The confidence field must be between 0 and 1.")

    if policy == "abstention_calibration_v1":
        abstained = parsed.get("abstained")
        if not isinstance(abstained, bool):
            raise UncertaintyResponseError("The abstained field must be a boolean.")
        if abstained and answer not in (None, ""):
            raise UncertaintyResponseError("An abstained response must not contain an answer.")
        if not abstained and (not isinstance(answer, str) or not answer.strip()):
            raise UncertaintyResponseError("A non-abstained response must contain an answer.")
    elif policy == "forced_answer_v1":
        abstained = False
        if not isinstance(answer, str) or not answer.strip():
            raise UncertaintyResponseError("The forced-answer baseline must provide an answer.")
    else:
        raise ValueError(f"Unsupported uncertainty policy: {policy}")

    return {
        "answer": answer.strip() if isinstance(answer, str) else None,
        "confidence": confidence,
        "abstained": abstained,
    }


def evaluate_uncertainty_case(
    expected_output: Any,
    raw_output: str,
    policy: str,
) -> dict[str, Any]:
    """Score answer/abstain behaviour and attempted-answer confidence separately."""
    validate_uncertainty_dataset_case(expected_output, context={"validated": True})
    parsed = parse_uncertainty_response(raw_output, policy)
    answerability = expected_output["answerability"]
    should_abstain = answerability != "answerable"
    abstained = parsed["abstained"]
    answer = parsed["answer"]

    answer_correct: bool | None = None
    if not abstained:
        if answerability == "answerable":
            from app.services.evaluator import normalize_answer

            normalized = normalize_answer(answer or "")
            answer_correct = any(
                normalized == normalize_answer(candidate)
                for candidate in expected_output["acceptable_answers"]
            )
        else:
            # The benchmark is closed-context: unsupported answers count as false answers.
            answer_correct = False

    decision_correct = abstained == should_abstain
    if answerability == "answerable" and abstained:
        failure_category = "unnecessary_abstention"
    elif answerability != "answerable" and not abstained:
        failure_category = "unsupported_answer"
    elif answerability == "answerable" and answer_correct is False:
        failure_category = "answer_mismatch"
    else:
        failure_category = None

    # Confidence means P(the proposed answer is correct and supported).
    # Abstentions have no proposed answer and are excluded from calibration metrics.
    brier_score = (
        round((parsed["confidence"] - float(answer_correct)) ** 2, 6)
        if answer_correct is not None
        else None
    )

    return {
        "score": 1.0 if decision_correct else 0.0,
        "confidence": parsed["confidence"],
        "abstained": abstained,
        "failure_category": failure_category,
        "metrics": {
            "scoring_method": policy,
            "answerability": answerability,
            "should_abstain": should_abstain,
            "decision_correct": decision_correct,
            "answer_correct": answer_correct,
            "confidence_target": answer_correct,
            "confidence_brier": brier_score,
            "parsed_answer": answer,
            "confidence_semantics": "probability_proposed_answer_is_correct_and_supported",
        },
    }


def summarize_uncertainty_cases(case_metrics: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    """Aggregate selective-answering, abstention, and confidence-calibration metrics."""
    total = len(case_metrics)
    valid = [item for item in case_metrics if item.get("response_valid", True)]
    answerable = [item for item in valid if item.get("answerability") == "answerable"]
    unanswerable = [item for item in valid if item.get("answerability") == "unanswerable"]
    underspecified = [item for item in valid if item.get("answerability") == "underspecified"]
    unknown = unanswerable + underspecified

    answered = [item for item in valid if not item.get("abstained", False)]
    abstained = [item for item in valid if item.get("abstained", False)]
    correct_decisions = sum(bool(item.get("decision_correct")) for item in valid)
    attempted_answerable = [
        item for item in answered if item.get("answerability") == "answerable"
    ]
    correct_abstentions = sum(bool(item.get("abstained")) for item in unknown)
    false_answers = sum(not bool(item.get("abstained")) for item in unknown)
    unnecessary_abstentions = sum(bool(item.get("abstained")) for item in answerable)

    calibration_rows = [
        item for item in answered
        if isinstance(item.get("confidence"), (int, float))
        and isinstance(item.get("answer_correct"), bool)
    ]
    brier_scores = [
        (float(item["confidence"]) - float(item["answer_correct"])) ** 2
        for item in calibration_rows
    ]

    bins = []
    for index in range(10):
        lower = index / 10
        upper = (index + 1) / 10
        bucket = [
            item for item in calibration_rows
            if lower <= float(item["confidence"]) < upper
            or (index == 9 and float(item["confidence"]) == 1.0)
        ]
        if bucket:
            bins.append({
                "lower": round(lower, 1),
                "upper": round(upper, 1),
                "count": len(bucket),
                "mean_confidence": round(
                    mean(float(item["confidence"]) for item in bucket), 4
                ),
                "empirical_accuracy": round(
                    mean(float(item["answer_correct"]) for item in bucket), 4
                ),
            })

    ece = (
        sum(
            (item["count"] / len(calibration_rows))
            * abs(item["mean_confidence"] - item["empirical_accuracy"])
            for item in bins
        )
        if calibration_rows
        else None
    )

    return {
        "evaluation_mode": policy,
        "total_cases": total,
        "valid_responses": len(valid),
        "invalid_responses": total - len(valid),
        "answerable_cases": len(answerable),
        "unanswerable_cases": len(unanswerable),
        "underspecified_cases": len(underspecified),
        "answered_cases": len(answered),
        "abstained_cases": len(abstained),
        "coverage": round(len(answered) / len(valid), 4) if valid else None,
        "decision_accuracy": round(correct_decisions / len(valid), 4) if valid else None,
        "answer_accuracy_on_attempted_answerable": (
            round(
                sum(item.get("answer_correct") is True for item in attempted_answerable)
                / len(attempted_answerable),
                4,
            )
            if attempted_answerable
            else None
        ),
        "unknown_abstention_recall": (
            round(correct_abstentions / len(unknown), 4) if unknown else None
        ),
        "false_answer_rate_on_unknown": (
            round(false_answers / len(unknown), 4) if unknown else None
        ),
        "unnecessary_abstention_rate": (
            round(unnecessary_abstentions / len(answerable), 4) if answerable else None
        ),
        "confidence_calibration_sample_size": len(calibration_rows),
        "confidence_brier_score": round(mean(brier_scores), 4) if brier_scores else None,
        "confidence_ece_10bin": round(ece, 4) if ece is not None else None,
        "confidence_bins": bins,
        "failure_categories": dict(
            Counter(
                item["failure_category"]
                for item in case_metrics
                if item.get("failure_category")
            )
        ),
        "metric_notes": {
            "coverage": "Fraction of valid responses that attempted an answer.",
            "unknown_abstention_recall": (
                "Fraction of valid unanswerable and underspecified cases correctly abstained."
            ),
            "false_answer_rate_on_unknown": (
                "Fraction of valid unanswerable and underspecified cases answered anyway."
            ),
            "unnecessary_abstention_rate": (
                "Fraction of valid answerable cases that the model unnecessarily abstained on."
            ),
            "confidence_brier_score": (
                "Mean squared error of self-reported confidence on attempted answers only."
            ),
            "confidence_ece_10bin": (
                "Equal-width 10-bin expected calibration error on attempted answers only."
            ),
            "answer_accuracy_on_attempted_answerable": (
                "Exact-match accuracy among answerable cases where the model answered."
            ),
        },
    }
