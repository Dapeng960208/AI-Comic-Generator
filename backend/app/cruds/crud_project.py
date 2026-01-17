from sqlmodel import Session, select
from app.models.models import Project, Character, StoryboardItem, GlobalConfig
from app.schemas.schemas import ProjectCreate, ProjectUpdate
from typing import List, Optional

def create_project(session: Session, project_in: ProjectCreate) -> Project:
    db_project = Project.model_validate(project_in)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

def get_projects(session: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    statement = select(Project).offset(skip).limit(limit).order_by(Project.updated_at.desc())
    return session.exec(statement).all()

def get_project(session: Session, project_id: str) -> Optional[Project]:
    return session.get(Project, project_id)

def update_project(session: Session, db_project: Project, project_in: ProjectUpdate) -> Project:
    project_data = project_in.model_dump(exclude_unset=True)
    for key, value in project_data.items():
        setattr(db_project, key, value)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)
    return db_project

def delete_project(session: Session, db_project: Project):
    session.delete(db_project)
    session.commit()

# Helpers for sub-entities
def create_global_config(session: Session, project_id: str, data: dict) -> GlobalConfig:
    # Check if exists
    statement = select(GlobalConfig).where(GlobalConfig.project_id == project_id)
    existing = session.exec(statement).first()
    if existing:
        existing.data = data
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    
    db_config = GlobalConfig(project_id=project_id, data=data)
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config

def save_characters(session: Session, project_id: str, characters_data: List[dict]) -> List[Character]:
    # Strategy: Clear existing or update? 
    # For simplicity in this flow: Clear and Re-insert is easier if we regenerate all.
    # But user might want to edit specific ones.
    # Better: Update by name match, create if new.
    
    results = []
    for char_data in characters_data:
        name = char_data.get("name")
        if not name: continue
        
        statement = select(Character).where(Character.project_id == project_id, Character.name == name)
        existing = session.exec(statement).first()
        
        if existing:
            existing.data = char_data
            session.add(existing)
            results.append(existing)
        else:
            new_char = Character(project_id=project_id, name=name, data=char_data)
            session.add(new_char)
            results.append(new_char)
            
    session.commit()
    return results

def save_storyboard(session: Session, project_id: str, storyboard_data: List[dict]) -> List[StoryboardItem]:
    # Similar strategy: Clear and Re-insert is risky if we have images.
    # But storyboard is sequential.
    # Let's delete all and re-insert for now as "Regenerate JSON" usually means fresh start.
    # IF the user is just editing JSON text, we replace everything.
    
    # Check if there are existing items with images we want to preserve?
    # Ideally, we should try to map them back, but it's hard if sequence changes.
    # For now: delete all items for this project and insert new.
    
    statement = select(StoryboardItem).where(StoryboardItem.project_id == project_id)
    existing_items = session.exec(statement).all()
    for item in existing_items:
        session.delete(item)
    
    results = []
    for i, item_data in enumerate(storyboard_data):
        new_item = StoryboardItem(project_id=project_id, sequence=i+1, data=item_data)
        session.add(new_item)
        results.append(new_item)
        
    session.commit()
    return results
