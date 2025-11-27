import json
import os
from typing import List
from src.core.entities import ColorCapture

class JsonColorRepository:
    def __init__(self, file_path: str = "colors.json"):
        self.file_path = file_path

    def save_all(self, colors: List[ColorCapture]):
        data = []
        for color in colors:
            data.append({
                "id": color.id,
                "hex": color.hex_code,
                "rgb": color.rgb_tuple
            })
        
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error guardando: {e}")

    def load_all(self) -> List[ColorCapture]:
        if not os.path.exists(self.file_path):
            return []
        
        results = []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for item in data:
                # Soporte para archivos viejos sin ID
                color_id = item.get("id") 
                
                # Reconstruir entidad
                # Si no tenía ID (versión vieja), el dataclass generará uno nuevo automáticamente
                # al omitir el argumento 'id' si es None, pero dataclass no funciona así directo.
                # Lo manejamos explícitamente:
                
                kwargs = {
                    "hex_code": item["hex"],
                    "rgb_tuple": tuple(item["rgb"])
                }
                if color_id:
                    kwargs["id"] = color_id
                    
                color = ColorCapture(**kwargs)
                results.append(color)
        except Exception as e:
            print(f"Error cargando (posible archivo corrupto, se iniciará vacío): {e}")
            return []
            
        return results