from dataclasses import dataclass

@dataclass
class ColorCapture:
    """Entidad que representa un color capturado."""
    hex_code: str
    rgb_tuple: tuple[int, int, int]
    
    def get_formatted(self, format_type: str) -> str:
        """Devuelve el string del color según el formato solicitado."""
        if format_type == "RGB":
            return f"{self.rgb_tuple}" # Salida: (255, 0, 0)
        # Por defecto HEX
        return self.hex_code