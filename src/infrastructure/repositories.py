import json
import os
from typing import List
from src.core.entities import ColorCapture

class JsonColorRepository:
    def __init__(self, file_path: str = "colors.json"):
        self.file_path = file_path

    def save_all(self, colors: List[ColorCapture]):
        data = [{"id": c.id, "hex": c.hex_code, "rgb": c.rgb_tuple} for c in colors]
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving: {e}")

    def load_all(self) -> List[ColorCapture]:
        if not os.path.exists(self.file_path):
            return []
        
        results = []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for item in data:
                kwargs = {
                    "hex_code": item["hex"], 
                    "rgb_tuple": tuple(item["rgb"])
                }
                if "id" in item:
                    kwargs["id"] = item["id"]
                results.append(ColorCapture(**kwargs))
        except Exception:
            return []
            
        return results