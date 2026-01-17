from sqlmodel import Session, select
from app.models.models import ModelConfig
from app.schemas.schemas import ModelConfigCreate, ModelConfigUpdate
from typing import List, Optional

def create_model_config(session: Session, config_in: ModelConfigCreate) -> ModelConfig:
    db_config = ModelConfig.model_validate(config_in)
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config

def get_model_configs(session: Session, skip: int = 0, limit: int = 100) -> List[ModelConfig]:
    statement = select(ModelConfig).offset(skip).limit(limit)
    return session.exec(statement).all()

def get_model_config(session: Session, config_id: int) -> Optional[ModelConfig]:
    return session.get(ModelConfig, config_id)

def update_model_config(session: Session, db_config: ModelConfig, config_in: ModelConfigUpdate) -> ModelConfig:
    config_data = config_in.model_dump(exclude_unset=True)
    for key, value in config_data.items():
        setattr(db_config, key, value)
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config

def delete_model_config(session: Session, db_config: ModelConfig):
    session.delete(db_config)
    session.commit()

def get_active_config(session: Session, model_type: str) -> Optional[ModelConfig]:
    statement = select(ModelConfig).where(ModelConfig.model_type == model_type, ModelConfig.is_active == True)
    return session.exec(statement).first()
