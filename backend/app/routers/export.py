import shutil
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.database import get_session
from app.models.models import Project
from app.services.image_service import split_comic_page

router = APIRouter()

@router.get("/{project_id}")
def export_project(
    project_id: str, 
    split_images: bool = False,
    session: Session = Depends(get_session)
):
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Check if any images generated
    has_images = any(item.image_url for item in project.storyboard_items) or any(c.image_url for c in project.characters)
    if not has_images:
        raise HTTPException(status_code=400, detail="No images generated yet. Cannot export.")
        
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_static_dir = os.path.join(base_dir, "static", project_id)
    export_dir = os.path.join(project_static_dir, "export")
    
    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)
    os.makedirs(export_dir)
    
    # Export Characters
    chars_dir = os.path.join(export_dir, "characters")
    os.makedirs(chars_dir)
    for char in project.characters:
        if char.image_url:
            # Resolve absolute path from relative URL
            # URL: /static/{project_id}/characters/xxx.png
            # Path: backend/static/{project_id}/characters/xxx.png
            # We can construct it directly if we know the structure, but let's parse url
            rel_path = char.image_url.lstrip("/") # static/...
            local_path = os.path.join(base_dir, rel_path.replace("/", os.sep))
            
            if os.path.exists(local_path):
                shutil.copy(local_path, os.path.join(chars_dir, f"{char.name}.png"))

    panels_dir = os.path.join(export_dir, "panels")
    if split_images:
        os.makedirs(panels_dir)
    
    # Sort items
    items = sorted(project.storyboard_items, key=lambda x: x.sequence)
    
    for item in items:
        if item.image_url:
            rel_path = item.image_url.lstrip("/")
            local_path = os.path.join(base_dir, rel_path.replace("/", os.sep))
            
            if os.path.exists(local_path):
                shutil.copy(local_path, os.path.join(export_dir, f"comic_part_{item.sequence}.png"))
                
                if split_images:
                    with open(local_path, "rb") as f:
                        img_bytes = f.read()
                    
                    try:
                        panels = split_comic_page(img_bytes)
                        for idx, panel_bytes in enumerate(panels):
                            p_name = f"panel_{item.sequence}_{idx+1}.png"
                            with open(os.path.join(panels_dir, p_name), "wb") as f:
                                f.write(panel_bytes)
                    except Exception as e:
                        print(f"Failed to split panel {item.id}: {e}")
                        
    zip_path_base = os.path.join(project_static_dir, "export_archive")
    shutil.make_archive(zip_path_base, 'zip', export_dir)
    
    return {"download_url": f"/static/{project_id}/export_archive.zip"}
