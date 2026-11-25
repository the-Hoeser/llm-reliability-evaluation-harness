import hashlib
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Dataset, DatasetVersion, TestCase
from app.db.session import get_db
from app.schemas import DatasetCreate, DatasetCreated, DatasetSummary

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetSummary])
def list_datasets(db: Session = Depends(get_db)) -> list[dict]:
    datasets = list(
        db.scalars(
            select(Dataset)
            .where(Dataset.is_archived.is_(False))
            .order_by(Dataset.created_at.desc())
        )
    )
    response = []
    for dataset in datasets:
        latest_version = db.scalar(
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset.id)
            .order_by(DatasetVersion.version.desc())
            .limit(1)
        )
        case_count = 0
        if latest_version is not None:
            case_count = db.scalar(
                select(func.count(TestCase.id)).where(
                    TestCase.dataset_version_id == latest_version.id
                )
            ) or 0
        response.append(
            {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "is_archived": dataset.is_archived,
                "latest_version_id": latest_version.id if latest_version else None,
                "latest_version": latest_version.version if latest_version else None,
                "test_case_count": case_count,
            }
        )
    return response


@router.post("", response_model=DatasetCreated, status_code=status.HTTP_201_CREATED)
def create_dataset(payload: DatasetCreate, db: Session = Depends(get_db)) -> DatasetCreated:
    canonical_cases = [case.model_dump(mode="json") for case in payload.test_cases]
    checksum = hashlib.sha256(
        json.dumps(canonical_cases, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    dataset = Dataset(name=payload.name, description=payload.description)
    db.add(dataset)
    db.flush()

    version = DatasetVersion(
        dataset_id=dataset.id,
        version=1,
        source="api",
        checksum=checksum,
        notes="Initial version created through the API.",
    )
    db.add(version)
    db.flush()

    db.add_all(
        [
            TestCase(
                dataset_version_id=version.id,
                external_id=case.external_id,
                input_text=case.input_text,
                expected_output=case.expected_output,
                context=case.context,
                tags=case.tags,
                case_metadata=case.case_metadata,
            )
            for case in payload.test_cases
        ]
    )
    db.commit()
    db.refresh(dataset)
    return DatasetCreated(
        id=dataset.id,
        name=dataset.name,
        description=dataset.description,
        version_id=version.id,
        version=version.version,
        checksum=checksum,
        test_case_count=len(payload.test_cases),
    )


@router.get("/{dataset_id}/versions")
def list_dataset_versions(dataset_id: UUID, db: Session = Depends(get_db)) -> list[dict]:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    versions = db.scalars(
        select(DatasetVersion)
        .where(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version.desc())
    )
    return [
        {
            "id": str(item.id),
            "dataset_id": str(item.dataset_id),
            "version": item.version,
            "source": item.source,
            "checksum": item.checksum,
            "created_at": item.created_at,
        }
        for item in versions
    ]
