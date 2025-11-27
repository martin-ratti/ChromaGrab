from src.core.entities import ColorCapture

class ColorTools:
    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        """Convierte una tupla RGB (255, 0, 0) a Hex '#FF0000'."""
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2]).upper()

def capture_color_use_case(screen_service, clipboard_service) -> ColorCapture:
    """
    Captura el color bajo el mouse, lo copia al clipboard y devuelve la entidad.
    """
    # 1. Obtener color RGB
    rgb = screen_service.get_color_at_cursor()
    
    # 2. Convertir a HEX
    hex_code = ColorTools.rgb_to_hex(rgb)
    
    # 3. Copiar al portapapeles
    clipboard_service.copy(hex_code)
    
    # 4. Retornar entidad
    return ColorCapture(hex_code=hex_code, rgb_tuple=rgb)