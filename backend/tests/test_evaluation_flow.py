from app.services.model_adapter import ModelResponse


class FakeAdapter:
    def generate(self, *, input_text, system_prompt, parameters, json_mode=False):
        if "capital of France" in input_text:
            return ModelResponse(output_text="Paris", prompt_tokens=8, completion_tokens=2)
        return ModelResponse(output_text="An unverified answer", prompt_tokens=6, completion_tokens=4)


def test_dataset_experiment_and_run_vertical_slice(client, monkeypatch) -> None:
    import app.services.execution as execution

    monkeypatch.setattr(execution, "build_model_adapter", lambda _model_config: FakeAdapter())

    dataset_response = client.post(
        "/api/datasets",
        json={
            "name": "Geography smoke test",
            "description": "Small test dataset for the first execution flow.",
            "test_cases": [
                {
                    "external_id": "geo-001",
                    "input_text": "What is the capital of France?",
                    "expected_output": "Paris",
                    "tags": ["geography", "smoke"],
                },
                {
                    "external_id": "geo-002",
                    "input_text": "Name a city in France.",
                    "expected_output": "Lyon",
                    "tags": ["geography"],
                },
            ],
        },
    )
    assert dataset_response.status_code == 201
    dataset = dataset_response.json()
    assert dataset["test_case_count"] == 2
    assert dataset["version"] == 1

    model_response = client.post(
        "/api/models",
        json={
            "name": "Test OpenAI-compatible model",
            "provider": "openai_compatible",
            "model_id": "example-model",
            "endpoint_url": "https://api.example.test/v1",
            "api_key_env": "TEST_MODEL_API_KEY",
            "parameters": {"temperature": 0},
        },
    )
    assert model_response.status_code == 201
    model_config = model_response.json()

    experiment_response = client.post(
        "/api/experiments",
        json={
            "name": "First reliability experiment",
            "dataset_version_id": dataset["version_id"],
            "model_config_id": model_config["id"],
            "system_prompt": "Answer briefly and precisely.",
            "evaluator_config": {"method": "normalized_exact_match"},
        },
    )
    assert experiment_response.status_code == 201
    experiment = experiment_response.json()

    run_response = client.post(f"/api/experiments/{experiment['id']}/runs")
    assert run_response.status_code == 201
    run = run_response.json()

    assert run["status"] == "completed"
    assert run["summary"]["total_cases"] == 2
    assert run["summary"]["scored"] == 2
    assert run["summary"]["mean_score"] == 0.5
    assert run["summary"]["failure_categories"] == {"answer_mismatch": 1}

    detail_response = client.get(f"/api/runs/{run['id']}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert len(detail["results"]) == 2
    assert detail["results"][0]["model_output"] == "Paris"
    assert detail["results"][0]["prompt_tokens"] == 8

    event_query = client.get("/api/runs/not-a-uuid")
    assert event_query.status_code == 422


def test_dataset_rejects_duplicate_test_case_ids(client) -> None:
    response = client.post(
        "/api/datasets",
        json={
            "name": "Invalid duplicate test data",
            "test_cases": [
                {"external_id": "same", "input_text": "Question one"},
                {"external_id": "same", "input_text": "Question two"},
            ],
        },
    )
    assert response.status_code == 422
