import json

from app.services.model_adapter import ModelResponse


class FakeUncertaintyAdapter:
    def generate(self, *, input_text, system_prompt, parameters, json_mode=False):
        assert json_mode is True
        if "capital of France" in input_text:
            payload = {"answer": "Paris", "confidence": 0.9, "abstained": False}
        else:
            payload = {"answer": None, "confidence": 0.05, "abstained": True}
        return ModelResponse(output_text=json.dumps(payload), prompt_tokens=12, completion_tokens=10)


class FakeForcedAnswerAdapter:
    def generate(self, *, input_text, system_prompt, parameters, json_mode=False):
        assert json_mode is True
        answer = "Paris" if "capital of France" in input_text else "A guessed budget"
        payload = {"answer": answer, "confidence": 0.8}
        return ModelResponse(output_text=json.dumps(payload), prompt_tokens=12, completion_tokens=10)


def _create_dataset_model_experiment(client, method: str):
    dataset_response = client.post(
        "/api/datasets",
        json={
            "name": f"{method} benchmark",
            "description": "Tiny closed-context smoke dataset.",
            "test_cases": [
                {
                    "external_id": "known-001",
                    "input_text": "What is the capital of France?",
                    "context": "The note states: The capital of France is Paris.",
                    "expected_output": {
                        "answerability": "answerable",
                        "acceptable_answers": ["Paris"],
                    },
                    "tags": ["answerable"],
                },
                {
                    "external_id": "unknown-001",
                    "input_text": "What was the exact project budget?",
                    "context": "The project note says the team approved the budget but does not state an amount.",
                    "expected_output": {"answerability": "unanswerable"},
                    "tags": ["unanswerable"],
                },
            ],
        },
    )
    assert dataset_response.status_code == 201, dataset_response.text
    dataset = dataset_response.json()

    model_response = client.post(
        "/api/models",
        json={
            "name": f"Fake adapter {method}",
            "provider": "openai_compatible",
            "model_id": "fake-evaluation-model",
            "endpoint_url": "https://fake.example/v1",
            "api_key_env": "FAKE_EVALUATION_KEY",
            "parameters": {"temperature": 0},
        },
    )
    assert model_response.status_code == 201, model_response.text
    model_config = model_response.json()

    experiment_response = client.post(
        "/api/experiments",
        json={
            "name": f"Research run {method}",
            "dataset_version_id": dataset["version_id"],
            "model_config_id": model_config["id"],
            "system_prompt": "Follow the experiment protocol exactly.",
            "evaluator_config": {"method": method},
        },
    )
    assert experiment_response.status_code == 201, experiment_response.text
    return experiment_response.json()


def test_abstention_experiment_persists_decisions_and_calibration(client, monkeypatch):
    import app.services.execution as execution

    monkeypatch.setattr(
        execution,
        "build_model_adapter",
        lambda _model_config: FakeUncertaintyAdapter(),
    )
    experiment = _create_dataset_model_experiment(client, "abstention_calibration_v1")

    run_response = client.post(f"/api/experiments/{experiment['id']}/runs")
    assert run_response.status_code == 201, run_response.text
    run = run_response.json()
    summary = run["summary"]

    assert run["status"] == "completed"
    assert summary["total_cases"] == 2
    assert summary["decision_accuracy"] == 1.0
    assert summary["coverage"] == 0.5
    assert summary["unknown_abstention_recall"] == 1.0
    assert summary["false_answer_rate_on_unknown"] == 0.0
    assert summary["answer_accuracy_on_attempted_answerable"] == 1.0
    assert summary["confidence_brier_score"] == 0.01
    assert summary["confidence_calibration_sample_size"] == 1

    detail_response = client.get(f"/api/runs/{run['id']}")
    assert detail_response.status_code == 200
    results = detail_response.json()["results"]
    assert results[0]["confidence"] == 0.9
    assert results[0]["abstained"] is False
    assert results[1]["abstained"] is True
    assert results[1]["failure_category"] is None


def test_forced_answer_baseline_records_false_answers(client, monkeypatch):
    import app.services.execution as execution

    monkeypatch.setattr(
        execution,
        "build_model_adapter",
        lambda _model_config: FakeForcedAnswerAdapter(),
    )
    experiment = _create_dataset_model_experiment(client, "forced_answer_v1")

    run_response = client.post(f"/api/experiments/{experiment['id']}/runs")
    assert run_response.status_code == 201, run_response.text
    summary = run_response.json()["summary"]

    assert summary["coverage"] == 1.0
    assert summary["unknown_abstention_recall"] == 0.0
    assert summary["false_answer_rate_on_unknown"] == 1.0
    assert summary["answer_accuracy_on_attempted_answerable"] == 1.0


def test_uncertainty_experiment_rejects_cases_without_context(client):
    dataset_response = client.post(
        "/api/datasets",
        json={
            "name": "Missing context",
            "test_cases": [
                {
                    "external_id": "no-context-001",
                    "input_text": "What is the answer?",
                    "expected_output": {
                        "answerability": "answerable",
                        "acceptable_answers": ["42"],
                    },
                }
            ],
        },
    )
    assert dataset_response.status_code == 201

    model_response = client.post(
        "/api/models",
        json={
            "name": "No context test model",
            "model_id": "fake-model",
            "api_key_env": "FAKE_KEY",
        },
    )
    assert model_response.status_code == 201

    response = client.post(
        "/api/experiments",
        json={
            "name": "Should not be created",
            "dataset_version_id": dataset_response.json()["version_id"],
            "model_config_id": model_response.json()["id"],
            "evaluator_config": {"method": "abstention_calibration_v1"},
        },
    )
    assert response.status_code == 422


def test_jsonl_import_creates_a_versioned_dataset(client):
    jsonl = "\n".join([
        json.dumps({
            "id": "jsonl-001",
            "input": "What is 2 + 2?",
            "context": "The note says two plus two equals four.",
            "expected_output": {
                "answerability": "answerable",
                "acceptable_answers": ["4", "four"],
            },
            "tags": ["arithmetic"],
        }),
        json.dumps({
            "id": "jsonl-002",
            "input": "What is the author's middle name?",
            "context": "The note identifies the author as Dana Reed and gives no middle name.",
            "expected_output": {"answerability": "unanswerable"},
            "tags": ["missing-evidence"],
        }),
    ])
    response = client.post(
        "/api/datasets/import-jsonl",
        params={"name": "Imported uncertainty benchmark"},
        files={"file": ("benchmark.jsonl", jsonl, "application/x-ndjson")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["test_case_count"] == 2
    assert response.json()["version"] == 1
