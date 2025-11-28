import PyInstaller.__main__
import customtkinter
import os
import shutil

# Configuración
APP_NAME = "ChromaGrab"
MAIN_SCRIPT = "main.py"
ICON_FILE = "icon.ico"

# Obtener ruta de customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

print("--- 🚀 INICIANDO COMPILACIÓN DE CHROMAGRAB ---")

# Limpieza
if os.path.exists("dist"): shutil.rmtree("dist")
if os.path.exists("build"): shutil.rmtree("build")
if os.path.exists(f"{APP_NAME}.spec"): os.remove(f"{APP_NAME}.spec")

# Argumentos
args = [
    MAIN_SCRIPT,
    f'--name={APP_NAME}',
    '--noconsole',
    '--onefile',
    '--clean',
    f'--icon={ICON_FILE}',  # 1. Icono del archivo .exe (Explorer)
    
    # 2. IMPORTANTE: Meter el icono ADENTRO del exe para usarlo en la ventana
    f'--add-data={ICON_FILE}{os.pathsep}.',
    
    f'--add-data={ctk_path}{os.pathsep}customtkinter',
]

PyInstaller.__main__.run(args)
print(f"\n✅ ¡ÉXITO! Tu ejecutable está en: dist/{APP_NAME}.exe")