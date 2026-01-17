from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session
from app.core.database import get_session
from app.models.models import Project, Character, StoryboardItem, Task, ImageHistory
from app.services.ai_service import AIService
from app.services.consistency_service import ConsistencyService
from app.utils.json_utils import extract_json_blocks
from app.cruds import crud_project
import os
import uuid
import json
import traceback

import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

def save_generated_image(session, project_id, entity_type, entity_id, image_bytes):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_static_dir = os.path.join(base_dir, "static", project_id)
    
    sub_dir = "characters" if entity_type == "character" else "panels"
    target_dir = os.path.join(project_static_dir, sub_dir)
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    filename = f"{entity_type}_{entity_id}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(target_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(image_bytes)
        
    relative_url = f"/static/{project_id}/{sub_dir}/{filename}"
    
    # Save History
    history = ImageHistory(
        project_id=project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        image_url=relative_url
    )
    session.add(history)
    
    return relative_url

router = APIRouter()

from app.core.prompts import COMIC_GENERATION_SYSTEM_PROMPT

def get_system_prompt():
    return COMIC_GENERATION_SYSTEM_PROMPT

# --- Background Task Functions ---

def generate_storyboard_task(task_id: str, project_id: str, user_input: str):
    logger.info(f"Starting storyboard generation task: {task_id} for project: {project_id}")
    # We need a fresh session for the background task
    from app.core.database import engine
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task: 
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = "processing"
        session.add(task)
        session.commit()
        
        try:
            project = crud_project.get_project(session, project_id)
            logger.info(f"Project found: {project.title}")
            
            # Save User Input (Persist it)
            project.story_input = user_input
            session.add(project)
            session.commit()
            
            ai = AIService(session)
            system_prompt = get_system_prompt()
            
            # Construct Final Prompt with Preferences
            final_prompt = user_input
            
            # --- Replace Placeholders in System Prompt ---
            system_prompt = get_system_prompt()
            
            # Defaults
            style = "Standard"
            if project.theme: style = project.theme
            
            lang = "English"
            if project.language:
                lang_map = {"zh-CN": "Simplified Chinese", "en-US": "English", "ja-JP": "Japanese"}
                lang = lang_map.get(project.language, project.language)
                
            # Inject into System Prompt
            system_prompt = system_prompt.replace("{User Specified Style}", style)
            # We could also inject language if we had a placeholder, but style is the main one failing.
            # Let's add language instruction to system prompt dynamically if needed, 
            # or rely on the "Language & Format" section in prompt which says "Use user input language".
            
            # --- Construct User Prompt ---
            final_prompt = user_input
            
            # Append preferences as normal requirements
            prefs = []
            if project.theme: prefs.append(f"Theme: {project.theme}")
            if project.language: prefs.append(f"Language: {project.language}")
            if project.panel_count: prefs.append(f"Estimated Panel Count: {project.panel_count}")
            if project.aspect_ratio: prefs.append(f"Aspect Ratio: {project.aspect_ratio}")
            
            if prefs:
                final_prompt += "\n\nRequirements:\n" + "\n".join(prefs)

            logger.info("Calling AI service for storyboard generation...")
            generated_text = ai.generate_storyboard(system_prompt, final_prompt)
            
            # --- Save Generated Text to Temp File ---
            import time
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            temp_dir = os.path.join(base_dir, "static", project_id, "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            timestamp = int(time.time())
            temp_file = os.path.join(temp_dir, f"ai_output_{timestamp}.txt")
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(generated_text)
                logger.info(f"Saved raw AI output to {temp_file}")
            except Exception as e:
                logger.error(f"Failed to save temp AI output: {e}")
            # ----------------------------------------

            logger.info("AI generation complete. Extracting JSON blocks...")
            json_blocks = extract_json_blocks(generated_text)
            
            char_blocks = [b for b in json_blocks if b.get("type") == "character_sheet"]
            story_blocks = [b for b in json_blocks if b.get("type") == "storyboard"] 
            
            if not story_blocks:
                 story_blocks = [b for b in json_blocks if b.get("type") not in ["character_sheet", "comic_config"]]

            # --- Missing Character Check & Fix ---
            story_char_names = set()
            for block in story_blocks:
                chars = block.get("characters", [])
                if isinstance(chars, str):
                    story_char_names.add(chars)
                elif isinstance(chars, list):
                    for c in chars:
                        if isinstance(c, str): story_char_names.add(c)
                        elif isinstance(c, dict): story_char_names.add(c.get("name", ""))

            generated_char_names = set(b.get("name") for b in char_blocks if b.get("name"))
            
            # Simple fuzzy matching or direct check
            missing_chars = []
            for name in story_char_names:
                # Check if name is contained in any generated char name (e.g. "Xiao Ming" vs "Ming")
                found = False
                for g_name in generated_char_names:
                    if name in g_name or g_name in name:
                        found = True
                        break
                if not found and name and len(name) > 1: # Ignore single chars or empty
                    missing_chars.append(name)
            
            if missing_chars:
                logger.info(f"Detected missing characters: {missing_chars}. Requesting AI to generate them...")
                fix_prompt = f"You missed generating character sheets for the following characters that appeared in the storyboard: {', '.join(missing_chars)}. Please generate 'character_sheet' JSON blocks for them now. Do not generate anything else."
                
                try:
                    fix_response = ai.generate_storyboard(system_prompt, fix_prompt) # Re-use generate method
                    fix_blocks = extract_json_blocks(fix_response)
                    new_chars = [b for b in fix_blocks if b.get("type") == "character_sheet"]
                    if new_chars:
                        logger.info(f"Successfully generated {len(new_chars)} missing characters.")
                        char_blocks.extend(new_chars)
                except Exception as e:
                    logger.error(f"Failed to generate missing characters: {e}")

            config_block = next((b for b in json_blocks if b.get("type") == "comic_config"), None)
            
            # If AI didn't return config, create one from project prefs
            if not config_block and (project.aspect_ratio or project.language):
                config_block = {
                    "type": "comic_config",
                    "style": "Standard", # Default
                    "aspect_ratio": project.aspect_ratio or "16:9",
                    "language": project.language or "en-US"
                }
            
            if config_block:
                crud_project.create_global_config(session, project_id, config_block)
            
            # --- Enforce Consistency: Update meta_info for all blocks ---
            # Re-read global config if we just created/updated it
            # Or use the config_block we have
            
            if not config_block:
                 # Try to fetch existing
                 # But we just generated it. If None, we create a default one above.
                 # Let's use the one we have.
                 pass

            if config_block:
                global_style = config_block.get("style", "")
                global_aspect = config_block.get("aspect_ratio", "16:9")
                global_lang = config_block.get("language", "en-US")
                
                # Update Character Sheets
                for char in char_blocks:
                    char["meta_info"] = char.get("meta_info", {})
                    char["meta_info"]["language"] = global_lang
                    char["meta_info"]["style"] = global_style
                    
                    # Remove top-level redundant keys if they exist to avoid confusion
                    char.pop("language", None)
                    char.pop("style", None)
                    
                # Update Storyboard Items
                for block in story_blocks:
                    meta = block.get("meta_info", {})
                    meta["style"] = global_style
                    meta["language"] = global_lang
                    meta["aspect_ratio"] = global_aspect
                    
                    # Also inject specific style configs if present
                    if "bubble_style" in config_block: meta["bubble_style"] = config_block["bubble_style"]
                    if "narration_style" in config_block: meta["narration_style"] = config_block["narration_style"]
                    if "border_style" in config_block: meta["border_style"] = config_block["border_style"]
                    if "gutter_style" in config_block: meta["gutter_style"] = config_block["gutter_style"]
                    if "layout_settings" in config_block: meta["layout_settings"] = config_block["layout_settings"]
                    
                    block["meta_info"] = meta
            
            # Save to DB
            crud_project.save_characters(session, project_id, char_blocks)
            crud_project.save_storyboard(session, project_id, story_blocks)
            
            # Consistency
            consistency = ConsistencyService(session)
            consistency.normalize_project(project_id)
            
            task.status = "completed"
            task.result = {"blocks_found": len(json_blocks)}
            task.progress = 100
            session.add(task)
            session.commit()
            logger.info(f"Storyboard task {task_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Storyboard task {task_id} failed: {e}")
            traceback.print_exc()
            task.status = "failed"
            task.message = str(e)
            session.add(task)
            session.commit()

def generate_all_images_task(task_id: str, project_id: str):
    logger.info(f"Starting batch image generation task: {task_id} for project: {project_id}")
    from app.core.database import engine
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task: 
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = "processing"
        session.add(task)
        session.commit()
        
        try:
            project = session.get(Project, project_id)
            ai = AIService(session)
            
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            static_root = os.path.join(base_dir, "static")
            if not os.path.exists(static_root): os.makedirs(static_root)

            # 1. Generate Characters
            total_chars = len(project.characters)
            logger.info(f"Generating {total_chars} characters...")
            for i, char in enumerate(project.characters):
                if char.image_url: 
                    logger.info(f"Character {char.name} already has image, skipping.")
                    continue 
                
                logger.info(f"Generating image for character: {char.name}")
                json_prompt = json.dumps(char.data, ensure_ascii=False, indent=2)
                json_prompt += "\n\n generate a character design sheet with 4 panels: front view, side view, clothing details, accessories."
                
                try:
                    image_bytes = ai.generate_image(json_prompt)
                    relative_url = save_generated_image(session, project_id, "character", char.id, image_bytes)
                    char.image_url = relative_url
                    session.add(char)
                    session.commit()
                    logger.info(f"Character {char.name} generated successfully.")
                except Exception as e:
                    logger.error(f"Failed to generate char {char.id}: {e}")
                    print(f"Failed to generate char {char.id}: {e}")
                
                # Update task progress (Characters are 20% of work?)
                # Let's simple split: chars + storyboard items
                
            # 2. Generate Storyboard Items (Sequential)
            # Re-fetch items to ensure order
            items = sorted(project.storyboard_items, key=lambda x: x.sequence)
            total_items = len(items)
            logger.info(f"Generating {total_items} storyboard panels...")
            
            generated_history = [] # Keep track of generated images for context
            
            # Populate history with existing images
            # Actually comic_generator logic builds history as it goes.
            # We should probably load existing images into history if we are resuming?
            # For "one click", let's assume we scan all items.
            
            for i, item in enumerate(items):
                task.progress = int((i / total_items) * 100)
                session.add(task)
                session.commit()
                
                if item.image_url:
                    # Add to history
                    filename = os.path.basename(item.image_url)
                    # We need to find where it is stored.
                    # Assuming standard structure
                    # We need absolute path for history
                    # item.image_url is like /static/{project_id}/panels/{filename}
                    rel_path = item.image_url.lstrip("/")
                    abs_path = os.path.join(base_dir, rel_path.replace("/", os.sep))
                    
                    if os.path.exists(abs_path):
                        generated_history.append(abs_path)
                    continue
                
                logger.info(f"Generating panel {item.sequence}...")
                
                # Prepare Context
                context_images = []
                
                # a) Character Sheets
                char_names = item.data.get("characters", [])
                if isinstance(char_names, str): char_names = [char_names]
                elif isinstance(char_names, list):
                    names = []
                    for c in char_names:
                        if isinstance(c, dict): names.append(c.get("name", ""))
                        elif isinstance(c, str): names.append(c)
                    char_names = names
                
                for name in char_names:
                    for p_char in project.characters:
                        if p_char.image_url and (p_char.name in name or name in p_char.name):
                            # Resolve absolute path for char image
                            rel_path = p_char.image_url.lstrip("/")
                            abs_path = os.path.join(base_dir, rel_path.replace("/", os.sep))
                            if os.path.exists(abs_path) and abs_path not in context_images:
                                context_images.append(abs_path)
                
                # b) Previous History (Last 3 logic)
                if len(generated_history) >= 3:
                    selected = [generated_history[0]] + generated_history[-2:]
                else:
                    selected = generated_history
                
                for path in selected:
                    if path not in context_images:
                        context_images.append(path)
                
                # Generate
                json_prompt = json.dumps(item.data, ensure_ascii=False, indent=2)
                json_prompt += "\n\n use json block as user input prompt to generate 2*2 grid comic image."
                
                try:
                    image_bytes = ai.generate_image(json_prompt, context_images)
                    relative_url = save_generated_image(session, project_id, "panel", item.id, image_bytes)
                    
                    item.image_url = relative_url
                    session.add(item)
                    session.commit()
                    
                    # Add to history (absolute path for context usage)
                    # We need absolute path for next context
                    # save_generated_image returns relative /static/...
                    # Reconstruct absolute path
                    # strip leading /
                    abs_path = os.path.join(base_dir, relative_url.lstrip("/").replace("/", os.sep))
                    generated_history.append(abs_path)
                    logger.info(f"Panel {item.sequence} generated successfully.")
                    
                except Exception as e:
                    logger.error(f"Failed to generate panel {item.id}: {e}")
                    print(f"Failed to generate panel {item.id}: {e}")
            
            task.status = "completed"
            task.progress = 100
            session.add(task)
            session.commit()
            logger.info(f"Batch generation task {task_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Batch generation task {task_id} failed: {e}")
            traceback.print_exc()
            task.status = "failed"
            task.message = str(e)
            session.add(task)
            session.commit()

def generate_all_characters_task(task_id: str, project_id: str):
    logger.info(f"Starting batch character generation task: {task_id} for project: {project_id}")
    from app.core.database import engine
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task: 
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = "processing"
        session.add(task)
        session.commit()
        
        try:
            project = session.get(Project, project_id)
            ai = AIService(session)
            
            total_chars = len(project.characters)
            logger.info(f"Generating {total_chars} characters...")
            
            for i, char in enumerate(project.characters):
                if char.image_url: 
                    logger.info(f"Character {char.name} already has image, skipping.")
                    continue 
                
                logger.info(f"Generating image for character: {char.name}")
                
                # Construct Natural Language Prompt from JSON
                data = char.data
                meta = data.get("meta_info", {})
                name = data.get("name", "Unknown")
                role = meta.get("role", "")
                age = meta.get("age", "")
                personality = data.get("personality", "") or meta.get("personality", "")
                style = meta.get("style", "")
                
                # Build Description from panels
                description = ""
                panels = data.get("design_panels", [])
                for p in panels:
                    view = p.get("view", "")
                    desc = p.get("description", "")
                    description += f"- {view}: {desc}\n"
                
                prompt = f"""Character Design Request:
Name: {name}
Role: {role}
Age: {age}
Personality: {personality}
Style: {style}

Visual Description:
{description}

Task: Generate a high-quality character reference sheet (Character Design) based on the above description. 
Include Front View, Side View, and detailed clothing/accessories. 
Ensure the character's expression and pose reflect their personality: {personality}.
"""
                
                try:
                    image_bytes = ai.generate_image(prompt)
                    relative_url = save_generated_image(session, project_id, "character", char.id, image_bytes)
                    char.image_url = relative_url
                    session.add(char)
                    session.commit()
                    logger.info(f"Character {char.name} generated successfully.")
                except Exception as e:
                    logger.error(f"Failed to generate char {char.id}: {e}")
                
                # Update progress
                progress = int(((i + 1) / total_chars) * 100)
                task.progress = progress
                session.add(task)
                session.commit()

            task.status = "completed"
            task.progress = 100
            session.add(task)
            session.commit()
            logger.info(f"Batch character generation task {task_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Batch character generation task {task_id} failed: {e}")
            traceback.print_exc()
            task.status = "failed"
            task.message = str(e)
            session.add(task)
            session.commit()

def generate_character_task(task_id: str, character_id: int):
    logger.info(f"Starting character generation task: {task_id} for char: {character_id}")
    from app.core.database import engine
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task: 
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = "processing"
        session.add(task)
        session.commit()
        
        try:
            char = session.get(Character, character_id)
            if not char:
                raise ValueError("Character not found")
                
            ai = AIService(session)
            
            # Construct Natural Language Prompt from JSON
            data = char.data
            meta = data.get("meta_info", {})
            name = data.get("name", "Unknown")
            role = meta.get("role", "")
            age = meta.get("age", "")
            personality = data.get("personality", "") or meta.get("personality", "")
            style = meta.get("style", "")
            
            # Build Description from panels
            description = ""
            panels = data.get("design_panels", [])
            for p in panels:
                view = p.get("view", "")
                desc = p.get("description", "")
                description += f"- {view}: {desc}\n"
            
            prompt = f"""Character Design Request:
Name: {name}
Role: {role}
Age: {age}
Personality: {personality}
Style: {style}

Visual Description:
{description}

Task: Generate a high-quality character reference sheet (Character Design) based on the above description. 
Include Front View, Side View, and detailed clothing/accessories. 
Ensure the character's expression and pose reflect their personality: {personality}.
"""
            
            logger.info(f"Calling AI service for character {char.name}...")
            image_bytes = ai.generate_image(prompt)
            
            relative_url = save_generated_image(session, char.project_id, "character", char.id, image_bytes)
            
            char.image_url = relative_url
            session.add(char)
            
            task.status = "completed"
            task.progress = 100
            session.add(task)
            session.commit()
            logger.info(f"Character task {task_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Character task {task_id} failed: {e}")
            traceback.print_exc()
            task.status = "failed"
            task.message = str(e)
            session.add(task)
            session.commit()

# --- Endpoints ---

from pydantic import BaseModel

class StoryboardRequest(BaseModel):
    user_input: str

@router.post("/storyboard/{project_id}")
def generate_storyboard(
    project_id: str, 
    request: StoryboardRequest, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    user_input = request.user_input
    logger.info(f"Received request to generate storyboard for project {project_id}")
    project = crud_project.get_project(session, project_id)
    if not project:
        logger.error(f"Project {project_id} not found")
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Save User Input Immediately
    project.story_input = user_input
    session.add(project)
    session.commit()
    
    # Create Task
    task = Task(
        type="storyboard", 
        status="pending", 
        project_id=project_id,
        name="Generate Storyboard",
        description=f"Generating storyboard based on user input..."
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    logger.info(f"Task created: {task.id}")
    
    background_tasks.add_task(generate_storyboard_task, task.id, project_id, user_input)
    
    return {"task_id": task.id}

@router.post("/all-images/{project_id}")
def generate_all_images(
    project_id: str, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    logger.info(f"Received request to generate all images for project {project_id}")
    project = crud_project.get_project(session, project_id)
    if not project:
        logger.error(f"Project {project_id} not found")
        raise HTTPException(status_code=404, detail="Project not found")
        
    task = Task(
        type="image_generation", 
        status="pending", 
        project_id=project_id,
        name="Batch Generate Images",
        description="Generating all storyboard images"
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    logger.info(f"Task created: {task.id}")
    
    background_tasks.add_task(generate_all_images_task, task.id, project_id)
    
    return {"task_id": task.id}

# Keep individual endpoints for manual control, but maybe make them async too?
# User asked for "Back task" for "generation". Usually implies the bulk actions.
# Single panel generation is usually fast enough (5-10s), but can be async if desired.
# For now, let's keep single endpoints sync for immediate feedback, or make them async if user insists "All generation".
# The prompt says "Generate text/image takes long time". 
# Let's keep single endpoints sync for simplicity of interaction (user waits 5s is ok), 
# but "One Click" and "Storyboard" are definitely async.

@router.post("/all-characters/{project_id}")
def generate_all_characters(
    project_id: str, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    logger.info(f"Received request to generate all characters for project {project_id}")
    project = crud_project.get_project(session, project_id)
    if not project:
        logger.error(f"Project {project_id} not found")
        raise HTTPException(status_code=404, detail="Project not found")
        
    task = Task(
        type="character_generation", 
        status="pending", 
        project_id=project_id,
        name="Batch Generate Characters",
        description="Generating all character design sheets"
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    logger.info(f"Task created: {task.id}")
    
    background_tasks.add_task(generate_all_characters_task, task.id, project_id)
    
    return {"task_id": task.id}

@router.post("/character/{character_id}")
def generate_character(
    character_id: int, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    char = session.get(Character, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
        
    task = Task(
        type="character_generation", 
        status="pending", 
        project_id=char.project_id,
        name=f"Draw Character: {char.name}",
        description=f"Drawing design sheet for character {char.name}"
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    background_tasks.add_task(generate_character_task, task.id, character_id)
    
    return {"task_id": task.id}

def generate_panel_task(task_id: str, item_id: int):
    logger.info(f"Starting panel generation task: {task_id} for item: {item_id}")
    from app.core.database import engine
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
            
        task.status = "processing"
        session.add(task)
        session.commit()
        
        try:
            item = session.get(StoryboardItem, item_id)
            if not item:
                 raise ValueError("Storyboard item not found")
            
            project = item.project
            ai = AIService(session)
            json_prompt = json.dumps(item.data, ensure_ascii=False, indent=2)
            json_prompt += "\n\n use json block as user input prompt to generate 2*2 grid comic image."
            
            context_images = []
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 1. Find Character Images
            char_names = item.data.get("characters", [])
            if isinstance(char_names, str): char_names = [char_names]
            elif isinstance(char_names, list):
                names = []
                for c in char_names:
                    if isinstance(c, dict): names.append(c.get("name", ""))
                    elif isinstance(c, str): names.append(c)
                char_names = names
        
            if project.characters:
                for name in char_names:
                    for p_char in project.characters:
                        if p_char.image_url and (p_char.name in name or name in p_char.name):
                            rel_path = p_char.image_url.lstrip("/")
                            abs_path = os.path.join(base_dir, rel_path.replace("/", os.sep))
                            if os.path.exists(abs_path) and abs_path not in context_images:
                                context_images.append(abs_path)
            
            # 2. Previous Panels
            prev_items = sorted([i for i in project.storyboard_items if i.sequence < item.sequence and i.image_url], key=lambda x: x.sequence)
            if prev_items:
                selected = []
                if len(prev_items) >= 3:
                    selected = [prev_items[0]] + prev_items[-2:]
                else:
                    selected = prev_items
                    
                for prev in selected:
                    rel_path = prev.image_url.lstrip("/")
                    abs_path = os.path.join(base_dir, rel_path.replace("/", os.sep))
                    if os.path.exists(abs_path) and abs_path not in context_images:
                        context_images.append(abs_path)
            
            # Style Consistency
            meta_style = item.data.get("meta_info", {}).get("style", "")
            if not meta_style and project.global_config:
                meta_style = project.global_config.data.get("style", "")
                
            if meta_style:
                 json_prompt += f"\n\nStyle Consistency Requirement: {meta_style}. Ensure the visual style matches the provided context images."
        
            logger.info(f"Calling AI service for panel {item.sequence}...")
            image_bytes = ai.generate_image(json_prompt, context_images)
            
            relative_url = save_generated_image(session, project.id, "panel", item.id, image_bytes)
            item.image_url = relative_url
            session.add(item)
            
            task.status = "completed"
            task.progress = 100
            session.add(task)
            session.commit()
            logger.info(f"Panel task {task_id} completed successfully.")
            
        except Exception as e:
            logger.error(f"Panel task {task_id} failed: {e}")
            traceback.print_exc()
            task.status = "failed"
            task.message = str(e)
            session.add(task)
            session.commit()

@router.post("/panel/{item_id}")
def generate_panel(
    item_id: int, 
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session)
):
    item = session.get(StoryboardItem, item_id)
    if not item:
         raise HTTPException(status_code=404, detail="Storyboard item not found")
         
    task = Task(
        type="image_generation", 
        status="pending", 
        project_id=item.project_id,
        name=f"Draw Panel: #{item.sequence}",
        description=f"Drawing panel {item.sequence}"
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    
    background_tasks.add_task(generate_panel_task, task.id, item_id)
    
    return {"task_id": task.id}
