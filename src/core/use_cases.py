from src.core.entities import ColorCapture

class ColorTools:
    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2]).upper()

def capture_color_use_case(screen_service) -> ColorCapture:
    """
    Solo captura y procesa el color. No tiene efectos secundarios (clipboard).
    """
    # 1. Obtener color RGB
    rgb = screen_service.get_color_at_cursor()
    
    # 2. Convertir a HEX
    hex_code = ColorTools.rgb_to_hex(rgb)
    
    # 3. Retornar entidad pura
    return ColorCapture(hex_code=hex_code, rgb_tuple=rgb)