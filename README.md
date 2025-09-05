# Gestión de Stock

Este proyecto Python automatiza la descarga, procesamiento y generación de informes de stock, así como la creación de archivos JSON para diversas aplicaciones.

## Características Principales

*   **Descarga y Procesamiento de Datos:** Obtiene y parsea informes de stock (`REPT_STOCK`).
*   **Carga y Fusión de Catálogos:** Carga catálogos de productos generales y especiales, y los fusiona con los datos de stock.
*   **Generación de Informes Excel:**
    *   **Reporte Histórico de Stock General (VES):** Genera un informe Excel con el histórico de stock referencial, incluyendo una columna de tendencia.
    *   **Reporte de Stock General por Línea:** Crea informes Excel detallados por línea de producto con formato de tabla.
    *   **Reporte de Códigos Especiales:** Genera un informe Excel para códigos especiales, incluyendo stock de almacenes y una columna de diferencia (Hoy - Ayer).
*   **Generación de Archivos JSON:**
    *   `productos_local.json`: Archivo JSON para aplicaciones web (IndexedDB).
    *   `stock_generales.json`: Archivo JSON para Firestore/Dialogflow con validación de esquema.
*   **Instantáneas Diarias de Stock:** Guarda un snapshot diario del stock consolidado para análisis histórico, asegurando que solo se tome una instantánea por día al inicio del proceso.

## Prerrequisitos

Asegúrate de tener instalado lo siguiente:

*   **Python 3.x**
*   **pip** (administrador de paquetes de Python)

Las dependencias específicas del proyecto se encuentran en `requirements.txt`.

## Configuración del Entorno

Sigue estos pasos para configurar el proyecto:

1.  **Clonar el Repositorio:**
    ```bash
    git clone https://github.com/tu_usuario/gestion_de_stock.git
    cd gestion_de_stock
    ```

2.  **Crear y Activar un Entorno Virtual:**
    Es altamente recomendable usar un entorno virtual para gestionar las dependencias del proyecto.
    ```bash
    python -m venv venv
    # En Windows
    .\venv\Scripts\activate
    # En macOS/Linux
    source venv/bin/activate
    ```

3.  **Instalar Dependencias:**
    Una vez activado el entorno virtual, instala todas las dependencias necesarias:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuración de Variables de Entorno:**
    Crea un archivo `.env` en la raíz del proyecto (al mismo nivel que `main.py`) basado en `.env.example`. Este archivo contendrá variables de entorno sensibles o específicas de tu configuración.

    Ejemplo de `.env.example`:
    ```
    SUNAT_API_TOKEN=tu_token_aqui
    # Otras variables de entorno si son necesarias
    ```
    Asegúrate de reemplazar `tu_token_aqui` con tu token real de la API de SUNAT.

## Uso

Para ejecutar el proceso completo de gestión de stock, simplemente ejecuta el script principal:

```bash
python main.py
```

El script realizará las siguientes operaciones en orden:
1.  Limpieza de archivos temporales.
2.  Carga y procesamiento de datos fuente.
3.  Consolidación de datos.
4.  Guardado de la instantánea diaria de stock (si no existe una para el día actual).
5.  Generación de todos los informes y archivos JSON.

## Estructura del Proyecto

```
.
├── .env.example             # Ejemplo de archivo de variables de entorno
├── .gitignore               # Archivos y directorios ignorados por Git
├── app.py                   # (Posiblemente lógica de aplicación o utilidades)
├── config.py                # Configuración del proyecto (rutas, etc.)
├── data_loader.py           # Funciones para cargar y procesar datos
├── main.py                  # Punto de entrada principal del script
├── README.md                # Este archivo
├── report_generator.py      # Funciones para generar los diferentes informes
├── requirements.txt         # Dependencias del proyecto
├── run_script.bat           # Script de Windows para ejecutar el proceso
├── schemas.py               # Definiciones de esquemas (e.g., Pydantic)
├── storage_manager.py       # (Posiblemente lógica de almacenamiento de datos)
├── utils.py                 # Funciones de utilidad
├── __pycache__/             # Caché de Python (ignorado por Git)
├── .git/                    # Repositorio Git (ignorado por Git)
├── datos/                   # Archivos de datos de entrada (ignorados por Git)
│   ├── base_total.xls
│   ├── codigos_especiales.xlsx
│   ├── codigos_generales.xlsx
│   └── lineas_a_procesar.xlsx
├── procesamiento/           # Archivos intermedios generados (ignorados por Git)
│   ├── historicos/
│   ├── logs/
│   └── temp/
├── salida/                  # Informes y archivos de salida generados (ignorados por Git)
├── storage_config/          # (Posiblemente configuración de almacenamiento)
└── venv/                    # Entorno virtual de Python (ignorado por Git)
```

## Configuración (`config.py`)

El archivo `config.py` contiene la configuración central del proyecto. Aquí se definen rutas de directorios, nombres de archivos de salida y otras configuraciones importantes.

*   `settings.REQUIRED_DIRS`: Directorios que el script creará si no existen.
*   `settings.OUTPUT_FINAL_REPORT_EXCEL`: Ruta del reporte de stock general.
*   `settings.OUTPUT_ESPECIALES_REPORT_EXCEL`: Ruta del reporte de códigos especiales.
*   `settings.OUTPUT_PRODUCTOS_LOCAL_JSON`: Ruta del archivo JSON para productos locales.
*   `settings.STOCK_GENERALES_FILE`: Ruta del archivo JSON de stock general.
*   `settings.HISTORICOS_DIR`: Directorio para guardar las instantáneas históricas de stock.
*   `settings.INPUT_ESPECIALES_EXCEL`: Ruta de la plantilla de códigos especiales.
*   `settings.DATA_STOCK_COMPLETO_FILE`: Ruta del archivo Excel con el stock consolidado.
*   `settings.TABLE_STYLES`: Estilos de tabla utilizados en los reportes Excel.

## Notas Importantes

*   **Instantáneas de Stock:** La función `save_daily_stock_snapshot` está diseñada para tomar una única instantánea del stock por día. Esto asegura la precisión de los datos históricos y de tendencia al comparar el stock inicial del día con el stock de días anteriores. Si el script se ejecuta varias veces en un mismo día, solo la primera ejecución creará la instantánea diaria.
*   **Archivos Ignorados:** Los directorios `datos/`, `procesamiento/` y `salida/` están configurados en `.gitignore` para no ser incluidos en el control de versiones de Git, ya que contienen datos de entrada, archivos intermedios y resultados generados, respectivamente.