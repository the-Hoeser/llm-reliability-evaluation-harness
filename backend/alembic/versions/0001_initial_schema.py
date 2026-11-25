"""Create the initial research schema.

Revision ID: 0001_initial_schema
"""
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE datasets (
            id UUID PRIMARY KEY,
            name VARCHAR(160) NOT NULL,
            description TEXT,
            is_archived BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_datasets_name ON datasets (name);

        CREATE TABLE dataset_versions (
            id UUID PRIMARY KEY,
            dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            source VARCHAR(40) NOT NULL DEFAULT 'manual',
            checksum VARCHAR(128),
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_dataset_versions_dataset_version UNIQUE (dataset_id, version)
        );
        CREATE INDEX ix_dataset_versions_dataset_id ON dataset_versions (dataset_id);

        CREATE TABLE test_cases (
            id UUID PRIMARY KEY,
            dataset_version_id UUID NOT NULL REFERENCES dataset_versions(id) ON DELETE CASCADE,
            external_id VARCHAR(160) NOT NULL,
            input_text TEXT NOT NULL,
            expected_output JSON,
            context JSON,
            tags JSON NOT NULL DEFAULT '[]',
            case_metadata JSON NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_test_cases_version_external_id UNIQUE (dataset_version_id, external_id)
        );
        CREATE INDEX ix_test_cases_dataset_version_id ON test_cases (dataset_version_id);

        CREATE TABLE model_configs (
            id UUID PRIMARY KEY,
            name VARCHAR(160) NOT NULL,
            provider VARCHAR(80) NOT NULL,
            model_id VARCHAR(160) NOT NULL,
            parameters JSON NOT NULL DEFAULT '{}',
            is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE experiments (
            id UUID PRIMARY KEY,
            name VARCHAR(180) NOT NULL,
            description TEXT,
            status VARCHAR(32) NOT NULL DEFAULT 'draft',
            dataset_version_id UUID NOT NULL REFERENCES dataset_versions(id),
            model_config_id UUID NOT NULL REFERENCES model_configs(id),
            evaluator_config JSON NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE evaluation_runs (
            id UUID PRIMARY KEY,
            experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
            status VARCHAR(32) NOT NULL DEFAULT 'queued',
            system_prompt_snapshot TEXT,
            model_config_snapshot JSON NOT NULL DEFAULT '{}',
            evaluator_config_snapshot JSON NOT NULL DEFAULT '{}',
            summary JSON NOT NULL DEFAULT '{}',
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_evaluation_runs_experiment_id ON evaluation_runs (experiment_id);

        CREATE TABLE test_results (
            id UUID PRIMARY KEY,
            run_id UUID NOT NULL REFERENCES evaluation_runs(id) ON DELETE CASCADE,
            test_case_id UUID NOT NULL REFERENCES test_cases(id),
            status VARCHAR(32) NOT NULL,
            model_output TEXT,
            score DOUBLE PRECISION,
            failure_category VARCHAR(80),
            metrics JSON NOT NULL DEFAULT '{}',
            latency_ms INTEGER,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_test_results_run_id ON test_results (run_id);
        CREATE INDEX ix_test_results_test_case_id ON test_results (test_case_id);
        CREATE INDEX ix_test_results_failure_category ON test_results (failure_category);

        CREATE TABLE execution_events (
            id UUID PRIMARY KEY,
            run_id UUID NOT NULL REFERENCES evaluation_runs(id) ON DELETE CASCADE,
            test_result_id UUID REFERENCES test_results(id) ON DELETE SET NULL,
            level VARCHAR(16) NOT NULL DEFAULT 'info',
            event_type VARCHAR(80) NOT NULL,
            message TEXT NOT NULL,
            details JSON NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_execution_events_run_id ON execution_events (run_id);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS execution_events;
        DROP TABLE IF EXISTS test_results;
        DROP TABLE IF EXISTS evaluation_runs;
        DROP TABLE IF EXISTS experiments;
        DROP TABLE IF EXISTS model_configs;
        DROP TABLE IF EXISTS test_cases;
        DROP TABLE IF EXISTS dataset_versions;
        DROP TABLE IF EXISTS datasets;
    """)
