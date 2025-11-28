from dataclasses import dataclass, field
import uuid

@dataclass
class ColorCapture:
    hex_code: str
    rgb_tuple: tuple[int, int, int]
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    
    def get_formatted(self, format_type: str) -> str:
        if format_type == "RGB":
            return f"{self.rgb_tuple}"
        return self.hex_code