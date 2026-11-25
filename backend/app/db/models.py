import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text,
    UniqueConstraint, Uuid, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Dataset(TimestampMixin, Base):
    __tablename__ = "datasets"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class DatasetVersion(TimestampMixin, Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version", name="uq_dataset_versions_dataset_version"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False, default="manual", server_default="manual")
    checksum: Mapped[str | None] = mapped_column(String(128))
    notes: Mapped[str | None] = mapped_column(Text)


class TestCase(TimestampMixin, Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        UniqueConstraint("dataset_version_id", "external_id", name="uq_test_cases_version_external_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dataset_versions.id", ondelete="CASCADE"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(160), nullable=False)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[Any | None] = mapped_column(JSON)
    context: Mapped[Any | None] = mapped_column(JSON)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    case_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")


class ModelConfig(TimestampMixin, Base):
    __tablename__ = "model_configs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model_id: Mapped[str] = mapped_column(String(160), nullable=False)
    endpoint_url: Mapped[str] = mapped_column(
        String(500), nullable=False, default="https://api.openai.com/v1",
        server_default="https://api.openai.com/v1",
    )
    api_key_env: Mapped[str] = mapped_column(
        String(100), nullable=False, default="OPENAI_API_KEY", server_default="OPENAI_API_KEY"
    )
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class Experiment(TimestampMixin, Base):
    __tablename__ = "experiments"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft")
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dataset_versions.id"), nullable=False)
    model_config_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_configs.id"), nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text)
    evaluator_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class EvaluationRun(TimestampMixin, Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", server_default="queued")
    system_prompt_snapshot: Mapped[str | None] = mapped_column(Text)
    model_config_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    evaluator_config_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TestResult(TimestampMixin, Base):
    __tablename__ = "test_results"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    test_case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_cases.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    model_output: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)
    failure_category: Mapped[str | None] = mapped_column(String(80), index=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)


class ExecutionEvent(TimestampMixin, Base):
    __tablename__ = "execution_events"
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluation_runs.id", ondelete="CASCADE"), index=True)
    test_result_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("test_results.id", ondelete="SET NULL")
    )
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info", server_default="info")
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
