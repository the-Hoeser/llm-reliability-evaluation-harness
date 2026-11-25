import re
from typing import Any


def normalize_answer(value: str) -> str:
    """Normalize casing and repeated whitespace; deliberately does not remove punctuation."""
    return re.sub(r"\s+", " ", value).strip().casefold()


def evaluate_output(expected_output: Any, model_output: str) -> dict[str, Any]:
    """Apply a transparent exact-match metric when the expected answer is a string.

    Other expected-output structures are intentionally left unscored until a suitable
    evaluator is explicitly selected. This avoids inventing a correctness signal.
    """
    if expected_output is None:
        return {
            "score": None,
            "failure_category": "unscored",
            "metrics": {"scoring_method": "none"},
        }

    if isinstance(expected_output, str):
        matched = normalize_answer(expected_output) == normalize_answer(model_output)
        return {
            "score": 1.0 if matched else 0.0,
            "failure_category": None if matched else "answer_mismatch",
            "metrics": {
                "scoring_method": "normalized_exact_match",
                "matched": matched,
            },
        }

    return {
        "score": None,
        "failure_category": "unscored",
        "metrics": {
            "scoring_method": "unsupported_expected_output",
            "expected_output_type": type(expected_output).__name__,
        },
    }
