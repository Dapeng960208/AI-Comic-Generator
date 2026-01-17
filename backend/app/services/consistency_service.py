import re
import json
import copy
from typing import List, Dict, Any
from sqlmodel import Session, select
from app.models.models import Project, Character, StoryboardItem, GlobalConfig

class ConsistencyService:
    def __init__(self, session: Session):
        self.session = session

    def normalize_project(self, project_id: str):
        """
        Normalizes the project's data (characters, storyboard) based on the global config.
        This mirrors the logic in comic_generator.py.
        """
        project = self.session.get(Project, project_id)
        if not project:
            return

        # Fetch all related data
        # Note: relationships are loaded if accessed, but let's be explicit if needed.
        # ProjectRead should handle loading, but here we work with ORM objects.
        
        global_config = project.global_config
        characters = project.characters
        storyboard_items = sorted(project.storyboard_items, key=lambda x: x.sequence)
        
        master_style = None
        master_meta = {}

        # Priority 0: Comic Config
        if global_config and global_config.data:
            config_data = global_config.data
            master_style = config_data.get("style")
            
            # Explicitly map all fields we want to sync
            master_meta = {
                "style": master_style,
                "bubble_style": config_data.get("bubble_style"),
                "narration_style": config_data.get("narration_style"),
                "border_style": config_data.get("border_style"),
                "gutter_style": config_data.get("gutter_style"),
                "layout_settings": config_data.get("layout_settings"),
                "aspect_ratio": config_data.get("aspect_ratio", "16:9"),
                "language": config_data.get("language", "English")
            }
        
        # Priority 1: First Character Sheet (if no config style)
        if not master_style and characters:
            # Try to find one with style
            for char in characters:
                if char.data.get("style"):
                    master_style = char.data.get("style")
                    break
        
        # Priority 2: First Story Block
        if storyboard_items:
            first_item = storyboard_items[0]
            first_meta = first_item.data.get("meta_info", {})
            if not master_style:
                master_style = first_meta.get("style")
            
            if not master_meta:
                master_meta = first_meta.copy()

        # Build Character Registry
        known_characters = {}
        for char in characters:
            full_name = char.name
            if not full_name: continue
            
            keywords = [full_name]
            simplified = re.split(r'[（\(]', full_name)[0].strip()
            if simplified and simplified != full_name:
                keywords.append(simplified)
            
            for kw in keywords:
                if kw:
                    known_characters[kw] = full_name

        # Apply Normalization
        # Even if master_style is None, we might still have layout_settings to sync
        # So we check if we have ANY master_meta to apply
        if master_meta:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Normalizing project {project_id} with master config: {json.dumps(master_meta, ensure_ascii=False)}")
            
            # 1. Normalize Characters
            for char in characters:
                char_data = copy.deepcopy(char.data)
                if not isinstance(char_data, dict):
                    char_data = dict(char_data)

                meta = char_data.get("meta_info", {})
                
                # Sync Core Fields
                if master_meta.get("style"): meta["style"] = master_meta.get("style")
                if master_meta.get("language"): meta["language"] = master_meta.get("language")
                if master_meta.get("aspect_ratio"): meta["aspect_ratio"] = master_meta.get("aspect_ratio")
                
                char_data["meta_info"] = meta
                
                # Cleanup top-level legacy fields
                char_data.pop("style", None)
                char_data.pop("language", None)
                char_data.pop("Language", None)
                
                char.data = char_data
                self.session.add(char)
            
            # 2. Normalize Storyboard Items
            total_volumes = len(storyboard_items)
            
            for i, item in enumerate(storyboard_items):
                # Use deepcopy to ensure we don't mutate the original object in place before assignment
                # and to ensure SQLAlchemy detects the change when we reassign.
                item_data = copy.deepcopy(item.data)
                if not isinstance(item_data, dict):
                    item_data = dict(item_data)
                
                # Check for missing characters
                plot_text = json.dumps(item_data.get("plot_breakdown", []), ensure_ascii=False)
                current_chars = item_data.get("characters", [])
                if isinstance(current_chars, str):
                    current_chars = [current_chars]
                if not isinstance(current_chars, list):
                    current_chars = []
                
                found_missing = []
                for kw, full_name in known_characters.items():
                    if kw in plot_text:
                        is_present = False
                        for char_name in current_chars:
                             if kw in char_name or char_name in full_name:
                                 is_present = True
                                 break
                        if not is_present:
                             if full_name not in current_chars and full_name not in found_missing:
                                 found_missing.append(full_name)
                
                if found_missing:
                    current_chars.extend(found_missing)
                    item_data["characters"] = current_chars

                # Sync Meta Info
                meta = item_data.get("meta_info", {})
                
                # We want to preserve existing fields in meta (like volume) but overwrite style configs
                # master_meta has style, bubble_style, etc.
                
                # Force update fields from master_meta even if they exist in meta
                # But careful with 'None' values in master_meta (though we constructed it from config)
                
                for key, value in master_meta.items():
                    if key == "volume": continue
                    
                    # Special handling for boolean values (like False in show_panel_numbers)
                    # "if value is not None" is correct for booleans.
                    # For nested dictionaries (like layout_settings), we should merge to preserve other keys.
                    
                    if value is not None:
                        if isinstance(value, dict) and isinstance(meta.get(key), dict):
                            meta[key].update(value)
                        else:
                            meta[key] = value
                    
                    # If value is None but key exists in master_meta keys (explicitly set to null), we might want to unset it?
                    # But our master_meta construction uses .get() defaults, so None usually means "not in config".
                    
                # Ensure Volume format
                meta["volume"] = f"{i+1}/{total_volumes}"
                item_data["meta_info"] = meta
                
                logger.info(f"Updated Item {i+1} meta: {json.dumps(meta, ensure_ascii=False)}")
                
                item.data = item_data
                self.session.add(item)
            
            self.session.commit()
