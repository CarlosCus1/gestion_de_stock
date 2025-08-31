# Proyecto de Automatización de Reportes de Stock

## Descripción

Este proyecto automatiza el proceso de descarga, consolidación y generación de reportes de stock a partir de diversas fuentes de datos. Incluye un proceso ETL (Extract, Transform, Load) para limpiar y unificar los datos, y genera reportes en formato Excel con formato profesional. Adicionalmente, cuenta con una aplicación web opcional para servir los reportes de forma segura.

## Características

- **Proceso ETL Automatizado:** Descarga y procesa reportes de stock de una API interna.
- **Consolidación de Datos:** Unifica datos de múltiples fuentes (API, catálogos de Excel, base de datos del ERP).
- **Generación de Reportes Profesionales:** Crea reportes en formato de tabla de Excel con estilos, filtros y anchos de columna ajustados.
- **Seguimiento Histórico:** Guarda snapshots diarios del stock de un almacén principal y genera reportes con la evolución del stock ("ayer" y "hace 1 semana").
- **Aplicación Web (Opcional):** Incluye una API con Flask para servir los reportes a través de URLs temporales y seguras, utilizando Google Cloud Storage.
- **Configuración Flexible:** La mayoría de los parámetros, rutas y nombres de archivo se pueden configurar en el archivo `config.py`.
- **Manejo de Errores y Logging:** Registra todo el proceso en archivos de log para facilitar la depuración.

## Estructura de Directorios

```
/
├── datos/                # Materia prima: catálogos y archivos base.
├── procesamiento/        # Archivos de trabajo: logs, históricos, datos intermedios.
│   ├── historicos/
│   └── logs/
├── salida/               # Reportes y archivos JSON finales para el usuario.
├── .gitignore            # Archivos y carpetas a ignorar por Git.
├── app.py                # Aplicación web con Flask.
├── config.py             # Archivo principal de configuración.
├── data_loader.py        # Funciones para cargar y parsear datos.
├── main.py               # Script principal que orquesta todo el proceso.
├── report_generator.py   # Funciones para generar los reportes.
├── requirements.txt      # Dependencias de Python.
└── schemas.py            # Esquemas de datos para validación.
```

## Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd codigos_cip
    ```

2.  **Crear un entorno virtual:**
    ```bash
    python -m venv venv
    ```

3.  **Activar el entorno virtual:**
    *   En Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   En macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Instalar las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuración de Entorno (.env)

Antes de ejecutar el proyecto, es necesario configurar las variables de entorno. Estos son secretos y configuraciones específicas de tu máquina que no deben subirse al repositorio.

1.  **Crear el archivo `.env`:**
    *   Busca el archivo `.env.example` en la raíz del proyecto.
    *   Crea una copia de este archivo y renómbrala a `.env`.

2.  **Editar el archivo `.env`:**
    *   Abre el archivo `.env` y añade los valores para las siguientes variables:
        ```
        # URL del API de Stock
        STOCK_API_URL="http://appweb.cipsa.com.pe:8054/..."

        # --- Google Cloud Storage (Opcional, para la App Web) ---
        # Nombre del bucket en Google Cloud Storage
        STORAGE_BUCKET_NAME="tu-bucket-name"
        # Ruta al archivo JSON de credenciales de Google Cloud
        STORAGE_CREDENTIALS_PATH="c:/ruta/a/tu/archivo/credenciales.json"
        ```

3.  **Importante:**
    *   El archivo `.env` está incluido en el `.gitignore`, por lo que nunca se subirá al repositorio.
    *   Asegúrate de que la ruta a tu archivo de credenciales JSON sea correcta y accesible por el script.

## Uso

### Ejecutar el Proceso ETL y Generar Reportes

Para ejecutar el proceso principal, simplemente corre el script `main.py`:

```bash
python main.py
```

El script realizará todo el proceso y generará los archivos finales en la carpeta `salida/` y los archivos de trabajo en `procesamiento/`.

### Ejecutar la Aplicación Web (Opcional)

Para iniciar el servidor web que sirve los reportes:

```bash
python app.py
```

La API estará disponible en `http://127.0.0.1:5000` por defecto.

## Configuración

El archivo `config.py` contiene todas las opciones de configuración del proyecto. Aquí puedes cambiar:
-   Las rutas de los directorios.
-   Los nombres de los archivos de entrada y salida.
-   La URL de la API de stock.
-   La columna de almacén para el seguimiento histórico (`HISTORICO_STOCK_COLUMN`).
-   Los estilos de las tablas de Excel.

```