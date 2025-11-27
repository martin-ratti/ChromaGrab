from dataclasses import dataclass

@dataclass
class ColorCapture:
    """Entidad que representa un color capturado."""
    hex_code: str
    rgb_tuple: tuple[int, int, int]
    
    @property
    def display_string(self) -> str:
        return f"{self.hex_code}  RGB{self.rgb_tuple}"