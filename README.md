# Sistema de Gestión de Stock

**Sistema ETL Unificado** que automatiza la descarga, procesamiento y generación de informes de stock. Genera TODOS los reportes en un solo directorio centralizado (`outputs/reports/`), eliminando resultados dispersos y proporcionando un manejo unificado de errores.

## Características Principales

*   **Descarga y Procesamiento de Datos:** Obtiene y parsea informes de stock (`REPT_STOCK`).
*   **Carga y Fusión de Catálogos:** Carga catálogos de productos generales y especiales, y los fusiona con los datos de stock.
*   **Generación de Informes Excel:**
    *   **Reporte Histórico de Stock General (VES):** Genera un informe Excel con el histórico de stock referencial, incluyendo una columna de tendencia.
    *   **Reporte de Stock General por Línea:** Crea informes Excel detallados por línea de producto con formato de tabla.
    *   **Reporte de Códigos Especiales:** Genera un informe Excel para códigos especiales, incluyendo stock de almacenes y una columna de diferencia (Hoy - Ayer).
    *   **Reporte de Colores por Código (`stock_color.xlsx`):** Genera un informe en formato Excel que desagrega el stock por color para cada código de producto. El script `scripts/generate_colores_json.py` procesa el reporte original (`STOCK_MODELO_COLOR.xls`), que a menudo contiene celdas combinadas, y lo transforma en un formato "tidy" o uniforme. En este formato, cada fila representa una combinación única de producto-color, repitiendo el código y la descripción del producto para cada color disponible. Esto facilita el análisis y la manipulación de los datos.
*   **Generación de Archivos JSON:**
    *   `productos_local.json`: Archivo JSON para aplicaciones web (IndexedDB).
    *   `stock_generales.json`: Archivo JSON para Firestore/Dialogflow con validación de esquema.
    *   `colores_por_codigo.json`: A partir del mismo proceso, se genera este archivo JSON. Agrupa todos los colores y sus respectivos stocks bajo una única clave, que es el código del producto. Esto proporciona una estructura anidada ideal para integraciones con aplicaciones web o APIs.
    *   `feriados.json`: Archivo JSON con feriados peruanos.
*   **Instantáneas Diarias de Stock:** Guarda un snapshot diario del stock consolidado para análisis histórico, asegurando que solo se tome una instantánea por día al inicio del proceso.
*   **Scripts Especializados:** Scripts independientes para generar reportes específicos (colores, feriados) con ejecución programada.

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

### Proceso Unificado (Recomendado)
Para ejecutar el proceso completo de gestión de stock, usa el orquestador unificado:

```bash
# Proceso completo unificado (recomendado)
python orchestrator.py --full-etl

# O usando el archivo .bat
run_stock_process.bat
```

El orquestador ejecuta automáticamente:
1. **ETL Principal** (`main.py`) - Descarga y procesa datos
2. **Scripts Especializados** - Genera reportes específicos
3. **Consolidación** - Unifica todos los resultados en `outputs/reports/`
4. **Entrega Automática** - Envía archivos a servidores configurados

### Scripts Individuales (Desarrollo)
Para desarrollo y pruebas específicas:

```bash
# ETL principal solo
python main.py

# Scripts especializados (solo cuando hay cambios)
python scripts/generate_colores_json.py   # Solo colores
python scripts/generate_feriados_json.py  # Solo feriados
```

### Lógica Inteligente del Sistema
El orquestador ejecuta procesos de manera inteligente:

- **📊 Stock (ETL Principal):** Siempre se ejecuta (datos diarios)
- **🎨 Colores:** Solo cuando cambian los datos de colores
- **📅 Feriados:** Solo cuando cambia el archivo de feriados

Esto optimiza el rendimiento y evita procesamiento innecesario.

### Programación Automática (Windows Task Scheduler)
Configura el orquestador para ejecución automática:
- **Proceso completo:** Una vez al día (7:00 AM)
- **Comando:** `python orchestrator.py --full-etl`
- **Directorio:** `C:\ruta\completa\al\proyecto`

## Archivos Generados

**TODOS los archivos se generan en un solo directorio unificado:** `outputs/reports/`

### Reportes Excel
- `reporte_stock_hoy.xlsx` - Reporte principal de stock diario
- `reporte_especiales.xlsx` - Reporte de códigos especiales
- `stock_color.xlsx` - Reporte de colores por código
- `reporte_historico_general_VES.xlsx` - Reporte histórico VES

### Archivos JSON
- `productos_local.json` - JSON para aplicaciones web (IndexedDB)
- `stock_generales.json` - JSON para Firestore/Dialogflow
- `colores_por_codigo.json` - JSON con stock por colores agrupado
- `feriados.json` - JSON con feriados peruanos

### Entrega Automática al Desktop
- `reporte_stock_hoy.xlsx` se copia automáticamente a `C:\Users\[usuario]\Desktop\`

## Estructura del Proyecto

```
.
├── .env.example             # Ejemplo de archivo de variables de entorno
├── .gitignore               # Archivos y directorios ignorados por Git
├── README.md                # Documentación del sistema unificado
├── requirements.txt         # Dependencias del proyecto
├── run_stock_process.bat    # 🚀 Proceso ETL completo unificado
├── orchestrator.py          # 🏗️ Orquestador principal (lógica inteligente)
├── main.py                  # 📊 ETL principal (descarga y procesa datos)
├── config/                  # ⚙️ Configuración centralizada
│   ├── unified_config.json  # Configuración unificada
│   └── config.py           # Configuración modular
├── modules/                 # 🔧 Módulos especializados
│   ├── etl_processor.py    # Procesador ETL
│   ├── report_generator.py # Generador de reportes
│   ├── file_delivery.py    # Sistema de entrega
│   └── data_validator.py   # Validador de datos
├── scripts/                 # 🐍 Scripts especializados
│   ├── run_complete_process.py
│   ├── generate_colores_json.py
│   ├── generate_feriados_json.py
│   └── scheduler_process.py
├── data_sources/            # 📥 Datos de entrada organizados
├── outputs/reports/         # 🎯 TODOS LOS RESULTADOS UNIFICADOS
├── procesamiento/           # 🔄 Archivos intermedios
├── logs/                    # 📋 Archivos de log
└── venv/                    # 🐍 Entorno virtual
```

## Configuración

### `config/unified_config.json` - Configuración Unificada
Archivo de configuración centralizada que controla todo el sistema:
- **Orquestador:** Configuración del sistema unificado
- **Reportes:** Definición de todos los tipos de reportes
- **Entrega:** Configuración de servidores de destino
- **Directorios:** Rutas centralizadas y flexibles

### `config/config.py` - Configuración Modular
Configuración específica para módulos especializados:
- **ETL Processor:** Configuración del procesamiento de datos
- **Report Generator:** Configuración de generación de reportes
- **File Delivery:** Configuración de entrega de archivos

### Variables Importantes
*   `outputs/reports/`: **Directorio unificado** para TODOS los resultados
*   `data_sources/`: Directorio de datos de entrada
*   `logs/`: Directorio de archivos de log
*   `procesamiento/`: Archivos intermedios de procesamiento

## Notas Importantes

*   **Sistema Unificado:** El orquestador (`orchestrator.py`) coordina TODOS los procesos y consolida los resultados en un solo directorio (`outputs/reports/`). Esto elimina la dispersión de archivos y proporciona un manejo centralizado de errores.

*   **Instantáneas de Stock:** La función `save_daily_stock_snapshot` toma una única instantánea del stock por día, asegurando precisión en los datos históricos y de tendencia.

*   **Directorio Unificado:** TODOS los archivos de resultado se generan en `outputs/reports/`, facilitando el acceso y mantenimiento.

*   **Entrega Automática:** Solo `reporte_stock_hoy.xlsx` se copia automáticamente al desktop del usuario.

*   **Arquitectura Modular:** Los módulos especializados (`etl_processor`, `report_generator`, `file_delivery`, `data_validator`) permiten mantenibilidad y escalabilidad.

*   **Archivos Ignorados:** Los directorios `data_sources/`, `procesamiento/`, `outputs/`, `logs/` y `temp/` están en `.gitignore` ya que contienen datos sensibles, intermedios y resultados generados.