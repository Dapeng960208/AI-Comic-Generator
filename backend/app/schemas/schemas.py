from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from app.models.models import (
    ModelConfigBase, ProjectBase, CharacterBase, StoryboardItemBase, GlobalConfigBase, TaskBase,
    ModelConfig, Project, Character, StoryboardItem, GlobalConfig, Task
)

# ModelConfig
class ModelConfigCreate(ModelConfigBase):
    pass

class ModelConfigUpdate(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    is_active: Optional[bool] = None

# Read Models for nested response
class CharacterRead(CharacterBase):
    id: int
    project_id: str

class StoryboardItemRead(StoryboardItemBase):
    id: int
    project_id: str

class GlobalConfigRead(GlobalConfigBase):
    id: int
    project_id: str

class TaskRead(TaskBase):
    id: str
    project_id: str
    created_at: datetime
    updated_at: datetime
    logs: List[str] = []

# Project
class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    story_input: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    panel_count: Optional[int] = None
    aspect_ratio: Optional[str] = None
    resolution: Optional[str] = None

class ProjectRead(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    characters: List[CharacterRead] = []
    storyboard_items: List[StoryboardItemRead] = []
    global_config: Optional[GlobalConfigRead] = None
