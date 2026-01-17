from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session
from typing import List, Dict
from pydantic import BaseModel
from app.core.database import get_session
from app.models.models import Project, GlobalConfig, Character, StoryboardItem
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectRead
from app.cruds import crud_project
from app.services.consistency_service import ConsistencyService

router = APIRouter()

@router.post("/", response_model=Project)
def create_project(project_in: ProjectCreate, session: Session = Depends(get_session)):
    return crud_project.create_project(session, project_in)

@router.get("/", response_model=List[Project])
def read_projects(skip: int = 0, limit: int = 100, session: Session = Depends(get_session)):
    return crud_project.get_projects(session, skip, limit)

@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: str, session: Session = Depends(get_session)):
    project = crud_project.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, project_in: ProjectUpdate, session: Session = Depends(get_session)):
    project = crud_project.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud_project.update_project(session, project, project_in)

@router.delete("/{project_id}")
def delete_project(project_id: str, session: Session = Depends(get_session)):
    project = crud_project.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    crud_project.delete_project(session, project)
    return {"ok": True}

# --- Data Management Endpoints ---

@router.put("/{project_id}/global_config")
def update_global_config(project_id: str, data: Dict = Body(...), session: Session = Depends(get_session)):
    project = crud_project.get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # 1. Update Project level fields first
    # This ensures consistency between project.theme/language and global_config
    if "language" in data:
        project.language = data["language"]
    if "style" in data:
        project.theme = data["style"]
    if "aspect_ratio" in data:
        project.aspect_ratio = data["aspect_ratio"]
        
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # 2. Update GlobalConfig in DB
    config = crud_project.create_global_config(session, project_id, data)
    
    # 3. Trigger consistency check (Propagate to all items)
    consistency = ConsistencyService(session)
    consistency.normalize_project(project_id)
    
    return config

@router.put("/{project_id}/characters/{char_id}")
def update_character(project_id: str, char_id: int, data: Dict = Body(...), session: Session = Depends(get_session)):
    char = session.get(Character, char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    char.data = data
    session.add(char)
    session.commit()
    session.refresh(char)
    
    # We might want to trigger consistency here too if character style changes, 
    # but primarily it's driven by global config.
    return char

@router.put("/{project_id}/storyboard/{item_id}")
def update_storyboard_item(project_id: str, item_id: int, data: Dict = Body(...), session: Session = Depends(get_session)):
    item = session.get(StoryboardItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Storyboard Item not found")
    
    item.data = data
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@router.delete("/{project_id}/characters/{char_id}")
def delete_character(project_id: str, char_id: int, session: Session = Depends(get_session)):
    char = session.get(Character, char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    
    session.delete(char)
    session.commit()
    return {"ok": True}

class MergeCharacterRequest(BaseModel):
    target_char_id: int
    source_char_ids: List[int]

@router.post("/{project_id}/characters/merge")
def merge_characters(
    project_id: str, 
    request: MergeCharacterRequest, 
    session: Session = Depends(get_session)
):
    target_char = session.get(Character, request.target_char_id)
    if not target_char:
        raise HTTPException(status_code=404, detail="Target character not found")
    
    source_chars = []
    for cid in request.source_char_ids:
        c = session.get(Character, cid)
        if c:
            source_chars.append(c)
    
    if not source_chars:
         raise HTTPException(status_code=400, detail="No valid source characters found")

    target_name = target_char.name
    source_names = [c.name for c in source_chars]
    
    # 1. Update Storyboard Items
    # We need to scan all items and replace source names with target name
    project = session.get(Project, project_id)
    if project.storyboard_items:
        for item in project.storyboard_items:
            data = item.data
            # 'characters' field in storyboard item data
            # It can be a list of strings, or list of dicts with 'name' key, or a single string
            chars = data.get("characters", [])
            
            new_chars = []
            modified = False
            
            # Helper to normalize input to list
            char_list = []
            if isinstance(chars, str): char_list = [chars]
            elif isinstance(chars, list): char_list = chars
            
            for c_entry in char_list:
                c_name = ""
                if isinstance(c_entry, str): c_name = c_entry
                elif isinstance(c_entry, dict): c_name = c_entry.get("name", "")
                
                # Check if this name matches any source name
                # Fuzzy match or exact? Let's do exact or containment for safety
                # User said "Ma Laoguanjia" vs "Ma Guanjia". 
                # Ideally we replace if it matches one of the source characters' name EXACTLY or close enough?
                # Since we selected source characters by ID, we know their names.
                # Let's replace if the name in storyboard matches a source character name.
                
                is_source = False
                for src_name in source_names:
                    if src_name == c_name: 
                        is_source = True
                        break
                
                if is_source:
                    # Replace with target name
                    # If entry was dict, update name field? Or just use string?
                    # Let's keep format.
                    if isinstance(c_entry, str):
                        new_chars.append(target_name)
                    elif isinstance(c_entry, dict):
                        c_entry['name'] = target_name
                        new_chars.append(c_entry)
                    modified = True
                else:
                    new_chars.append(c_entry)
            
            if modified:
                # Deduplicate if target name already existed?
                # Simple dedup for strings
                final_chars = []
                seen = set()
                for c in new_chars:
                    n = c if isinstance(c, str) else c.get("name", "")
                    if n not in seen:
                        final_chars.append(c)
                        seen.add(n)
                
                data['characters'] = final_chars
                item.data = data
                session.add(item)
    
    # 2. Delete Source Characters
    for c in source_chars:
        session.delete(c)
        
    session.commit()
    return {"ok": True, "merged_count": len(source_chars)}
