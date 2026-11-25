from app.services.evaluator import evaluate_output, normalize_answer


def test_normalize_answer_folds_case_and_whitespace() -> None:
    assert normalize_answer("  New  YORK\nCity ") == "new york city"


def test_exact_match_returns_one_for_normalized_match() -> None:
    result = evaluate_output("The answer", "  the   ANSWER ")
    assert result["score"] == 1.0
    assert result["failure_category"] is None
    assert result["metrics"]["scoring_method"] == "normalized_exact_match"


def test_exact_match_marks_mismatch_without_claiming_hallucination() -> None:
    result = evaluate_output("Expected answer", "Different answer")
    assert result["score"] == 0.0
    assert result["failure_category"] == "answer_mismatch"


def test_unsupported_ground_truth_is_not_scored() -> None:
    result = evaluate_output({"must_include": ["one", "two"]}, "one two")
    assert result["score"] is None
    assert result["failure_category"] == "unscored"
