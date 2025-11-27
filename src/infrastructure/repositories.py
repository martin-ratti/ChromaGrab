import json
import os
from typing import List
from src.core.entities import ColorCapture

class JsonColorRepository:
    """Repositorio para guardar/cargar colores en un archivo JSON."""
    
    def __init__(self, file_path: str = "colors.json"):
        self.file_path = file_path

    def save_all(self, colors: List[ColorCapture]):
        """Guarda la lista de objetos ColorCapture en el archivo."""
        data = []
        for color in colors:
            data.append({
                "hex": color.hex_code,
                "rgb": color.rgb_tuple
            })
        
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error guardando historial: {e}")

    def load_all(self) -> List[ColorCapture]:
        """Carga los colores del archivo."""
        if not os.path.exists(self.file_path):
            return []
        
        results = []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            for item in data:
                # Reconstruimos la entidad. 
                # Nota: JSON guarda tuplas como listas, convertimos de nuevo a tuple.
                color = ColorCapture(
                    hex_code=item["hex"],
                    rgb_tuple=tuple(item["rgb"]) 
                )
                results.append(color)
        except Exception as e:
            print(f"Error cargando historial: {e}")
            
        return results