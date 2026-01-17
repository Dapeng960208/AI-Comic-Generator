from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.models import ImageHistory, Character, StoryboardItem

router = APIRouter()

@router.get("/{entity_type}/{entity_id}")
def get_history(entity_type: str, entity_id: int, session: Session = Depends(get_session)):
    # entity_type: 'character' or 'panel'
    statement = select(ImageHistory).where(
        ImageHistory.entity_type == entity_type,
        ImageHistory.entity_id == entity_id
    ).order_by(ImageHistory.created_at.desc())
    history = session.exec(statement).all()
    return history

@router.post("/select/{history_id}")
def select_image(history_id: int, session: Session = Depends(get_session)):
    history = session.get(ImageHistory, history_id)
    if not history:
        raise HTTPException(status_code=404, detail="History item not found")
        
    if history.entity_type == "character":
        entity = session.get(Character, history.entity_id)
    elif history.entity_type == "panel": 
        entity = session.get(StoryboardItem, history.entity_id)
    else:
        raise HTTPException(status_code=400, detail="Unknown entity type")
        
    if not entity:
         raise HTTPException(status_code=404, detail="Entity not found")
         
    entity.image_url = history.image_url
    session.add(entity)
    session.commit()
    session.refresh(entity)
    return {"status": "success", "image_url": entity.image_url}
