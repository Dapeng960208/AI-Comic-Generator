from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List
from app.core.database import get_session
from app.models.models import ModelConfig
from app.schemas.schemas import ModelConfigCreate, ModelConfigUpdate
from app.cruds import crud_config

router = APIRouter()

@router.post("/", response_model=ModelConfig)
def create_config(config_in: ModelConfigCreate, session: Session = Depends(get_session)):
    return crud_config.create_model_config(session, config_in)

@router.get("/", response_model=List[ModelConfig])
def read_configs(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    return crud_config.get_model_configs(session, skip, limit)

@router.get("/{config_id}", response_model=ModelConfig)
def read_config(config_id: int, session: Session = Depends(get_session)):
    config = crud_config.get_model_config(session, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@router.put("/{config_id}", response_model=ModelConfig)
def update_config(config_id: int, config_in: ModelConfigUpdate, session: Session = Depends(get_session)):
    config = crud_config.get_model_config(session, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return crud_config.update_model_config(session, config, config_in)

@router.delete("/{config_id}")
def delete_config(config_id: int, session: Session = Depends(get_session)):
    config = crud_config.get_model_config(session, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    crud_config.delete_model_config(session, config)
    return {"ok": True}
