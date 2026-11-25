import json

import pytest

from app.services.uncertainty import (
    UncertaintyResponseError,
    evaluate_uncertainty_case,
    parse_uncertainty_response,
    summarize_uncertainty_cases,
    validate_uncertainty_dataset_case,
)


def test_dataset_validation_requires_context_and_answerability_label() -> None:
    expected = {"answerability": "answerable", "acceptable_answers": ["Paris"]}
    with pytest.raises(ValueError, match="non-empty context"):
        validate_uncertainty_dataset_case(expected, None)
    with pytest.raises(ValueError, match="answerability"):
        validate_uncertainty_dataset_case({"answerability": "maybe"}, "passage")


def test_dataset_validation_requires_reference_for_answerable_case() -> None:
    with pytest.raises(ValueError, match="acceptable_answers"):
        validate_uncertainty_dataset_case(
            {"answerability": "answerable", "acceptable_answers": []},
            "The context.",
        )


def test_abstention_case_rewards_supported_answer_and_abstention() -> None:
    expected_answer = {
        "answerability": "answerable",
        "acceptable_answers": ["Paris", "Paris, France"],
    }
    answer = evaluate_uncertainty_case(
        expected_answer,
        json.dumps({"answer": "PARIS", "confidence": 0.9, "abstained": False}),
        "abstention_calibration_v1",
    )
    assert answer["score"] == 1.0
    assert answer["metrics"]["answer_correct"] is True
    assert answer["metrics"]["confidence_brier"] == 0.01

    expected_unknown = {"answerability": "unanswerable"}
    abstention = evaluate_uncertainty_case(
        expected_unknown,
        json.dumps({"answer": None, "confidence": 0.05, "abstained": True}),
        "abstention_calibration_v1",
    )
    assert abstention["score"] == 1.0
    assert abstention["abstained"] is True
    assert abstention["failure_category"] is None
    assert abstention["metrics"]["confidence_brier"] is None


def test_answering_unknown_context_is_a_false_answer() -> None:
    result = evaluate_uncertainty_case(
        {"answerability": "unanswerable"},
        json.dumps({"answer": "A confident guess", "confidence": 0.95, "abstained": False}),
        "abstention_calibration_v1",
    )
    assert result["score"] == 0.0
    assert result["failure_category"] == "unsupported_answer"
    assert result["metrics"]["confidence_target"] is False
    assert result["metrics"]["confidence_brier"] == 0.9025


def test_forced_answer_baseline_does_not_claim_to_abstain() -> None:
    result = evaluate_uncertainty_case(
        {"answerability": "underspecified"},
        json.dumps({"answer": "A guess", "confidence": 0.7}),
        "forced_answer_v1",
    )
    assert result["abstained"] is False
    assert result["failure_category"] == "unsupported_answer"


@pytest.mark.parametrize(
    "raw_output",
    [
        "I do not know.",
        '{"answer": "Paris", "confidence": 1.2, "abstained": false}',
        '{"answer": null, "confidence": 0.5, "abstained": false}',
        '{"answer": "Paris", "confidence": 0.8, "abstained": "no"}',
    ],
)
def test_invalid_structured_outputs_are_rejected(raw_output: str) -> None:
    with pytest.raises(UncertaintyResponseError):
        parse_uncertainty_response(raw_output, "abstention_calibration_v1")


def test_summary_excludes_invalid_responses_from_rate_denominators() -> None:
    cases = [
        {
            "answerability": "answerable",
            "response_valid": True,
            "abstained": False,
            "decision_correct": True,
            "answer_correct": True,
            "confidence": 0.9,
        },
        {
            "answerability": "unanswerable",
            "response_valid": True,
            "abstained": True,
            "decision_correct": True,
            "answer_correct": None,
            "confidence": 0.1,
        },
        {
            "answerability": "unanswerable",
            "response_valid": False,
            "abstained": None,
            "confidence": None,
            "failure_category": "invalid_response_format",
        },
    ]
    summary = summarize_uncertainty_cases(cases, "abstention_calibration_v1")
    assert summary["total_cases"] == 3
    assert summary["valid_responses"] == 2
    assert summary["invalid_responses"] == 1
    assert summary["unknown_abstention_recall"] == 1.0
    assert summary["false_answer_rate_on_unknown"] == 0.0
