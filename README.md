<div align="center">

# 🎨 ChromaGrab - Professional Color Picker

<img src="https://img.shields.io/badge/Estado-Estable-success?style=for-the-badge&logo=check&logoColor=white" alt="Estado Badge"/>
<img src="https://img.shields.io/badge/Versión-3.0.0-blue?style=for-the-badge" alt="Version Badge"/>
<img src="https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge" alt="License Badge"/>

<br/>

<a href="https://github.com/martin-ratti" target="_blank" style="text-decoration: none;">
    <img src="https://img.shields.io/badge/👤%20Martín%20Ratti-martin--ratti-000000?style=for-the-badge&logo=github&logoColor=white" alt="Martin"/>
</a>

<br/>

<p>
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge"/>
    <img src="https://img.shields.io/badge/Arquitectura-Clean%20Arch-orange?style=for-the-badge&logo=expertsexchange&logoColor=white" alt="Clean Arch Badge"/>
    <img src="https://img.shields.io/badge/GUI-CustomTkinter-2B2B2B?style=for-the-badge&logo=tkinter&logoColor=white" alt="CustomTkinter Badge"/>
    <img src="https://img.shields.io/badge/Capture-MSS-blue?style=for-the-badge&logo=windows&logoColor=white" alt="MSS Badge"/>
    <img src="https://img.shields.io/badge/Hooks-Pynput-yellow?style=for-the-badge&logo=python&logoColor=black" alt="Pynput Badge"/>
</p>

</div>

---

## 🎯 Objetivo y Alcance

**ChromaGrab** es una herramienta de ingeniería de precisión diseñada para desarrolladores y diseñadores que necesitan capturar colores de cualquier parte de su pantalla (Multi-Monitor) instantáneamente.

A diferencia de los pickers web o básicos, ChromaGrab está construido para ser **invisible pero omnipresente**. Utiliza hooks de teclado globales, renderizado optimizado de alto rendimiento y persistencia de datos local, eliminando la fricción entre ver un color y tenerlo en el portapapeles.

---

## 🏛️ Arquitectura y Diseño

El proyecto sigue estrictamente los principios de **Clean Architecture**, garantizando un desacoplamiento total entre la lógica de captura y la interfaz gráfica.

### Diagrama de Capas

| Capa | Componente | Responsabilidad |
| :--- | :--- | :--- |
| **Interface** | `src/interface/gui.py` | Gestión de UI Reactiva, Modo Compacto/Expandido y Lupa. No contiene lógica de negocio. |
| **Core** | `src/core/use_cases.py` | Lógica pura: Conversión RGB a HEX y creación de entidades inmutables. |
| **Infrastructure** | `src/infrastructure/` | Implementación técnica "sucia": Captura de pantalla (`MSS`), Sonido (`Winsound`), Teclado (`Pynput`) y Persistencia (`JSON`). |

-----

## 🚀 Características Principales

* **⚡ Captura Instantánea (MSS):** Motor de captura basado en `mss`, capaz de leer píxeles en configuraciones multi-monitor y 4K con escalado DPI sin latencia.
* **🔬 Lupa de Precisión (Zero-Lag):** Ventana flotante con zoom 8x y retícula de píxel central. Optimizada mediante reciclaje de canvas para mantener 60 FPS sin fugas de memoria.
* **📏 Modo Barra (Compacto):** La interfaz se transforma en una micro-barra flotante "Always on Top" para no estorbar durante el flujo de diseño.
* **💾 Persistencia Automática:** Historial de colores ilimitado guardado en JSON local. Nunca pierdes una referencia.
* **🧠 UX Sensorial:**
    * **Feedback Visual:** Los botones parpadean en verde (Check) al copiar.
    * **Feedback Auditivo:** Sonido electrónico sutil al capturar.
    * **Smart Delete:** Borrado quirúrgico O(1) de elementos en la lista sin redibujar toda la UI.

-----

## 🛠️ Modo de Uso

```text
/ChromaGrab
├── main.py               <-- Punto de entrada
├── colors.json           <-- Base de datos local (Autogenerada)
└── icon.ico              <-- Icono de la aplicación
````

### Atajos Globales

| Tecla | Acción | Descripción |
| :--- | :--- | :--- |
| **`INSERT`** | **Capturar** | Guarda el color bajo el mouse y lo copia al portapapeles (HEX). |
| **`Alt + Z`** | **Lupa** | Activa/Desactiva la ventana de zoom flotante. |

### Interfaz

1.  **Copiar:** Haz clic en los botones **HEX** o **RGB** de la lista para copiar ese formato.
2.  **Modo Barra:** Haz clic en la flecha `↗` arriba a la derecha para minimizar la interfaz.
3.  **Fijar Ventana:** Usa el switch para mantener la app siempre por encima de otras ventanas.

-----

## 🧑‍💻 Setup para Desarrolladores

Si deseas contribuir o compilar tu propia versión:

### 1\. Configuración del Entorno

```bash
# Clonar repositorio
git clone [https://github.com/martin-ratti/ChromaGrab.git](https://github.com/martin-ratti/ChromaGrab.git)

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2\. Ejecución en Desarrollo

```bash
python main.py
```

### 3\. Compilación (Build .exe)

Para generar un ejecutable único y portable que incluya el icono:

```bash
pyinstaller --onefile --noconsole --icon=icon.ico --name="ChromaGrab" main.py
```

-----

## ⚖️ Créditos

Desarrollado por **Martín Ratti**.

  * **UI Framework:** CustomTkinter.
  * **Core Engine:** MSS & Pillow.
  * **Input Hooks:** Pynput.

