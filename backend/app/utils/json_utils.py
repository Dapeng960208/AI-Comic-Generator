import json
import re
from typing import List, Dict, Any

def extract_json_blocks(text: str) -> List[Dict[str, Any]]:
    """Extracts JSON blocks from the generated text."""
    json_blocks = []
    
    # 1. Try to find ```json ... ``` blocks
    pattern = r"```(?:json|JSON)?\s*(.*?)\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    
    # 2. If no code blocks found, or even if found, we should also look for raw JSON objects
    # because sometimes models output mixed content.
    # But let's stick to code blocks first if they exist.
    
    if not matches:
        # Fallback: Try to find top-level JSON objects/arrays directly in text
        # This regex looks for { ... } or [ ... ] that span multiple lines
        # It's not perfect but better than nothing
        # We search for anything starting with { or [ and ending with } or ]
        # non-greedy match might be safer for multiple blocks
        raw_pattern = r"(\{[\s\S]*?\}|\[[\s\S]*?\])"
        matches = re.findall(raw_pattern, text)
    
    def repair_json(json_str: str) -> Dict[str, Any]:
        """Attempts to repair common JSON errors, specifically missing commas."""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
            
        repaired_str = json_str
        max_attempts = 10 
        
        for _ in range(max_attempts):
            try:
                return json.loads(repaired_str)
            except json.JSONDecodeError as e:
                # print(f"JSON Decode Error at {e.pos}: {e.msg}")
                if "Expecting ',' delimiter" in str(e) or "Expecting property name enclosed in double quotes" in str(e):
                    pos = e.pos
                    search_str = repaired_str[:pos]
                    match = re.search(r'([\"}\]0-9])\s*$', search_str)
                    
                    if match:
                        insert_idx = match.end()
                        repaired_str = repaired_str[:insert_idx] + "," + repaired_str[insert_idx:]
                        continue
                
                # If we can't fix it, re-raise
                raise e
                
        return json.loads(repaired_str)

    for match in matches:
        if not match.strip(): continue
        # Simple heuristic to filter out non-json text blocks that might be caught by raw regex
        if not (match.strip().startswith('{') or match.strip().startswith('[')):
            continue
            
        try:
            data = repair_json(match)
            if isinstance(data, list):
                 json_blocks.extend(data)
            elif isinstance(data, dict):
                 json_blocks.append(data)
        except Exception as e:
            print(f"Failed to parse a JSON block: {e}")
            # print(f"Block content: {match[:100]}...")
            
    return json_blocks
