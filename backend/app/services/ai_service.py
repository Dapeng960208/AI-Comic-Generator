import os
import time
from typing import List, Optional
from sqlmodel import Session
from app.models.models import ModelConfig
from google import genai
from google.genai import types
from PIL import Image
import io

class AIService:
    def __init__(self, session: Session):
        self.session = session
        
    def _get_client(self, model_type: str):
        from app.cruds.crud_config import get_active_config
        config = get_active_config(self.session, model_type)
        
        if not config:
            raise ValueError(f"No active configuration found for {model_type} model.")
            
        if config.provider.lower() == "google":
            # Initialize Google Client
            return genai.Client(api_key=config.api_key), config.model_name
            
        raise NotImplementedError(f"Provider {config.provider} not supported yet.")

    def generate_storyboard(self, system_prompt: str, user_input: str) -> str:
        client, model_name = self._get_client("text")
        
        full_prompt = f"{system_prompt}\n\nUser Input: {user_input}\n\nPlease generate the full storyboard in JSON format as requested."
        
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            print(f"Error generating storyboard: {e}")
            raise e

    def generate_image(self, prompt: str, context_images: List[str] = None, aspect_ratio: str = "16:9", resolution: str = "2K") -> bytes:
        client, model_name = self._get_client("image")
        
        contents = [prompt]
        if context_images:
            for img_path in context_images:
                if os.path.exists(img_path):
                    try:
                        prev_img = Image.open(img_path)
                        contents.append(prev_img)
                    except Exception as e:
                        print(f"Failed to load context image {img_path}: {e}")
                else:
                    # Log missing context image but don't fail, just skip it
                    print(f"Warning: Context image not found at {img_path}, skipping.")

        # Retry loop
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        image_config=types.ImageConfig(
                            aspect_ratio=aspect_ratio,
                            image_size=resolution
                        ),
                    )
                )
                
                if response.parts:
                    for part in response.parts:
                        if part.inline_data is not None:
                            image_data = part.inline_data.data
                            if len(image_data) > 0:
                                return image_data
                            else:
                                print(f"Warning: Received empty image data on attempt {attempt + 1}")
                
                # Check for text refusal/error
                if response.text:
                    print(f"Model response text (no image): {response.text}")
                    
                print(f"Attempt {attempt + 1} failed: No valid image data found in response.")
                if attempt == max_retries - 1:
                    raise ValueError(f"No image found in response after {max_retries} retries. Last response: {response.text if response.text else 'Empty'}")
                
                time.sleep(2 ** attempt)
                
            except Exception as e:
                print(f"Error generating image (Attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise e
        return b""
