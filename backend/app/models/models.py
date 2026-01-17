from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from datetime import datetime
import uuid

# --- Base Models ---

class ModelConfigBase(SQLModel):
    provider: str
    api_key: str
    base_url: Optional[str] = None
    model_name: str
    model_type: str
    is_active: bool = True

class ProjectBase(SQLModel):
    title: str
    description: Optional[str] = None
    story_input: Optional[str] = None
    # Generation Preferences
    theme: Optional[str] = None
    language: Optional[str] = "zh-CN"
    panel_count: Optional[int] = 16
    aspect_ratio: Optional[str] = "16:9"
    resolution: Optional[str] = "2K"

class CharacterBase(SQLModel):
    name: str
    data: Dict = Field(default={}, sa_column=Column(JSON))
    image_url: Optional[str] = None

class StoryboardItemBase(SQLModel):
    sequence: int
    data: Dict = Field(default={}, sa_column=Column(JSON))
    image_url: Optional[str] = None

class GlobalConfigBase(SQLModel):
    data: Dict = Field(default={}, sa_column=Column(JSON))

class TaskBase(SQLModel):
    type: str # 'storyboard', 'image_generation', 'export'
    status: str # 'pending', 'processing', 'completed', 'failed'
    progress: int = 0 # 0-100
    message: Optional[str] = None
    logs: List[str] = Field(default=[], sa_column=Column(JSON))
    name: Optional[str] = None
    description: Optional[str] = None
    result: Dict = Field(default={}, sa_column=Column(JSON))

class ImageHistoryBase(SQLModel):
    entity_type: str # 'character' or 'storyboard_item'
    entity_id: int
    image_url: str
    
# --- Table Models ---

class ModelConfig(ModelConfigBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class Project(ProjectBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    characters: List["Character"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete"})
    storyboard_items: List["StoryboardItem"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete"})
    global_config: Optional["GlobalConfig"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete"})
    tasks: List["Task"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete"})
    image_history: List["ImageHistory"] = Relationship(back_populates="project", sa_relationship_kwargs={"cascade": "all, delete"})

class Character(CharacterBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="characters")

class StoryboardItem(StoryboardItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="storyboard_items")

class GlobalConfig(GlobalConfigBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="global_config")

class Task(TaskBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Project = Relationship(back_populates="tasks")

class ImageHistory(ImageHistoryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: str = Field(foreign_key="project.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    project: Project = Relationship(back_populates="image_history")
