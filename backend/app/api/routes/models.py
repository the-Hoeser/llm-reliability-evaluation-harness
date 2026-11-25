from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModelConfig
from app.db.session import get_db
from app.schemas import ModelConfigCreate, ModelConfigRead

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=list[ModelConfigRead])
def list_models(db: Session = Depends(get_db)) -> list[ModelConfig]:
    return list(db.scalars(select(ModelConfig).order_by(ModelConfig.created_at.desc())))


@router.post("", response_model=ModelConfigRead, status_code=status.HTTP_201_CREATED)
def create_model(payload: ModelConfigCreate, db: Session = Depends(get_db)) -> ModelConfig:
    existing = db.scalar(
        select(ModelConfig).where(
            ModelConfig.name == payload.name,
            ModelConfig.model_id == payload.model_id,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="A model configuration with this name and model already exists.")

    model_config = ModelConfig(**payload.model_dump())
    db.add(model_config)
    db.commit()
    db.refresh(model_config)
    return model_config
