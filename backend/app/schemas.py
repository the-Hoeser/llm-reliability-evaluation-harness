from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
SUPPORTED_EVALUATORS = {"normalized_exact_match"}
SUPPORTED_MODEL_PARAMETERS = {"temperature", "top_p", "max_tokens", "seed"}


class TestCaseCreate(BaseModel):
    external_id: ShortText
    input_text: ShortText
    expected_output: Any | None = None
    context: Any | None = None
    tags: list[str] = Field(default_factory=list)
    case_metadata: dict[str, Any] = Field(default_factory=dict)


class DatasetCreate(BaseModel):
    name: ShortText
    description: str | None = None
    test_cases: list[TestCaseCreate] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def external_ids_must_be_unique(self) -> "DatasetCreate":
        identifiers = [case.external_id for case in self.test_cases]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Each test case external_id must be unique within a dataset version.")
        return self


class DatasetCreated(BaseModel):
    id: UUID
    name: str
    description: str | None
    version_id: UUID
    version: int
    checksum: str
    test_case_count: int


class DatasetSummary(BaseModel):
    id: UUID
    name: str
    description: str | None
    is_archived: bool
    latest_version_id: UUID | None
    latest_version: int | None
    test_case_count: int


class ModelConfigCreate(BaseModel):
    name: ShortText
    provider: str = Field(default="openai_compatible", pattern="^openai_compatible$")
    model_id: ShortText
    endpoint_url: str = "https://api.openai.com/v1"
    api_key_env: str = Field(default="OPENAI_API_KEY", pattern="^[A-Z][A-Z0-9_]{1,99}$")
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("endpoint_url")
    @classmethod
    def endpoint_must_be_http_url(cls, value: str) -> str:
        cleaned = value.strip().rstrip("/")
        if not cleaned.startswith(("https://", "http://")):
            raise ValueError("endpoint_url must begin with https:// or http://")
        return cleaned

    @field_validator("parameters")
    @classmethod
    def parameters_must_be_supported(cls, value: dict[str, Any]) -> dict[str, Any]:
        unsupported = set(value) - SUPPORTED_MODEL_PARAMETERS
        if unsupported:
            names = ", ".join(sorted(unsupported))
            raise ValueError(f"Unsupported model parameters: {names}")
        return value


class ModelConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    provider: str
    model_id: str
    endpoint_url: str
    api_key_env: str
    parameters: dict[str, Any]
    is_enabled: bool


class ExperimentCreate(BaseModel):
    name: ShortText
    description: str | None = None
    dataset_version_id: UUID
    model_config_id: UUID
    system_prompt: str | None = None
    evaluator_config: dict[str, Any] = Field(
        default_factory=lambda: {"method": "normalized_exact_match"}
    )

    @model_validator(mode="after")
    def evaluator_must_be_supported(self) -> "ExperimentCreate":
        method = self.evaluator_config.get("method", "normalized_exact_match")
        if method not in SUPPORTED_EVALUATORS:
            raise ValueError(
                "The first release supports only the normalized_exact_match evaluator."
            )
        self.evaluator_config = {"method": method}
        return self


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None
    status: str
    dataset_version_id: UUID
    model_config_id: UUID
    system_prompt: str | None
    evaluator_config: dict[str, Any]


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    experiment_id: UUID
    status: str
    summary: dict[str, Any]
    started_at: datetime | None
    completed_at: datetime | None


class TestResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    test_case_id: UUID
    status: str
    model_output: str | None
    score: float | None
    failure_category: str | None
    metrics: dict[str, Any]
    latency_ms: int | None
    prompt_tokens: int | None
    completion_tokens: int | None
    error_message: str | None


class RunDetail(RunRead):
    results: list[TestResultRead]
