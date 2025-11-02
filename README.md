EADME.md</path>
<content"># Sistema de Gestión de Stock

**Sistema ETL Unificado y Resiliente** que automatiza la descarga, procesamiento y generación de informes de stock con **alta disponibilidad**, **recuperación automática** e **integración inteligente con Desktop**. Genera TODOS los reportes en un solo directorio centralizado (`outputs/reports/`), con entrega dual opcional a Google Drive.

## ✨ Mejoras Implementadas

### 🚀 **Resiliencia y Recuperación**
- **Descarga API con reintentos**: Hasta 3 reintentos con timeout progresivo
- **Fallback automático**: Usa datos anteriores si la API falla
- **Detección de cambios**: Solo procesa cuando hay datos nuevos
- **Recuperación automática**: Se reintenta sin intervención manual

### 📱 **Automatización Desktop Inteligente** (NUEVO)
- **Procesamiento automático**: Detecta archivos en Desktop automáticamente
- **Lógica "una vez y elimina"**: Procesa archivo una sola vez y lo elimina del Desktop
- **Parser de apóstrofe integrado**: Detecta códigos por apóstrofe con formato robusto
- **Filtrado por códigos válidos**: Usa catálogo de 1,097 códigos oficiales
- **Verificación inteligente**: Compara timestamps y decide automáticamente
- **Mantenimiento de resultados**: Mantiene reportes anteriores cuando no hay archivo nuevo

### 📤 **Entrega Dual Inteligente**
- **Archivos originales**: Se mantienen en `outputs/reports/`
- **Copias sincronizadas**: Opcional a Google Drive para compartir
- **Manejo de errores**: Continúa aunque falle la copia secundaria
- **Reintentos programados**: Si Google Drive no está disponible

### 🔧 **Portabilidad Mejorada**
- **Rutas relativas**: Funciona en cualquier directorio
- **Multiplataforma**: Compatible con Windows/Linux/Mac
- **Configuración portable**: Variables de entorno flexibles
- **Template incluido**: `.env.example` para nuevos usuarios

## 🎯 Nueva Funcionalidad Desktop

### 📱 **Flujo de Trabajo Automatizado**
```
07:00 AM - Usuario coloca STOCK_MODELO_COLOR.xls en Desktop
    ↓
08:00 AM - Sistema ejecuta automáticamente vía Programador de Tareas
    ↓
08:05 AM - Sistema detecta, procesa y elimina archivo:
    ├── 🔍 Detecta archivo en C:\Users\ccusi\Desktop\STOCK_MODELO_COLOR.xls
    ├── ⚡ Procesa con parser de apóstrofe integrado
    ├── 🎯 Filtra por 1,097 códigos válidos
    ├── 📊 Genera stock_color.xlsx y colores_por_codigo.json
    ├── 📅 Registra timestamp de procesamiento
    └── 🗑️ Elimina archivo del Desktop automáticamente
    ↓
09:00-23:00 - Sistema mantiene resultados anteriores
```

### 🔧 **Configuración Desktop**
- **Archivo fuente**: `C:\Users\ccusi\Desktop\STOCK_MODELO_COLOR.xls`
- **Catálogo de códigos**: `data_sources/catalogs/codigos_generales.xlsx` (1,097 códigos)
- **Archivos generados**: `stock_color.xlsx`, `colores_por_codigo.json`
- **Control**: `logs/desktop_colors_processed.json`

### ⏰ **Programación Automática**
```cmd
# Configuración Windows Task Scheduler
Nombre: StockProcess_Desktop
Acción: Iniciar un programa
Programa: C:\Windows\System32\cmd.exe
Argumentos: /c "C:\ruta\completa\run_stock_process.bat"
Horario: Diario a las 8:00 AM
```

## Características Principales

### 🔄 **Procesamiento Resiliente**
*   **Descarga API con Reintentos:** Hasta 3 reintentos con timeout progresivo (30s → 60s → 120s)
*   **Fallback Automático:** Usa datos del día/semana anterior si la API falla
*   **Detección de Cambios:** Solo procesa cuando hay datos nuevos significativos
*   **Recuperación Automática:** Se reintenta sin intervención manual

### 📱 **Automatización Desktop** (NUEVO)
*   **Detección Automática:** Monitorea Desktop para archivos de stock
*   **Procesamiento Inteligente:** Solo cuando detecta archivos nuevos o modificados
*   **Lógica "Una Vez":** Procesa una sola vez por día y elimina archivo fuente
*   **Parser Robusto:** Reconoce códigos por apóstrofe y formatos especiales
*   **Filtrado Oficial:** Solo códigos presentes en catálogo autorizado
*   **Mantenimiento Automático:** Preserva resultados durante el día

### 📊 **Procesamiento de Datos**
*   **Descarga y Procesamiento de Datos:** Obtiene y parsea informes de stock (`REPT_STOCK`) con validación
*   **Carga y Fusión de Catálogos:** Carga catálogos de productos generales y especiales, y los fusiona con los datos de stock
*   **Validación de Integridad:** Verifica que los datos descargados sean útiles y consistentes

### 📈 **Generación de Informes Excel**
*   **Reporte Histórico de Stock General (VES):** Genera un informe Excel con el histórico de stock referencial, incluyendo una columna de tendencia
*   **Reporte de Stock General por Línea:** Crea informes Excel detallados por línea de producto con formato de tabla
*   **Reporte de Códigos Especiales:** Genera un informe Excel para códigos especiales, incluyendo stock de almacenes y una columna de diferencia (Hoy - Ayer)
*   **Reporte de Colores por Código (`stock_color.xlsx`):** Genera un informe en formato Excel que desagrega el stock por color para cada código de producto

### 📋 **Generación de Archivos JSON**
*   `productos_local.json`: Archivo JSON para aplicaciones web (IndexedDB)
*   `stock_generales.json`: Archivo JSON para Firestore/Dialogflow con validación de esquema
*   `colores_por_codigo.json`: JSON con stock por colores agrupado por código
*   `feriados.json`: Archivo JSON con feriados peruanos

### 💾 **Gestión de Datos Históricos**
*   **Instantáneas Diarias de Stock:** Guarda un snapshot diario del stock consolidado para análisis histórico
*   **Una Instantánea por Día:** Asegura que solo se tome una instantánea por día al inicio del proceso
*   **Histórico Inteligente:** Mantiene datos históricos para fallback y análisis de tendencias

### 📤 **Entrega Dual Inteligente**
*   **Archivos Originales:** Se mantienen en `outputs/reports/` (proyecto)
*   **Copias Sincronizadas:** Opcional a Google Drive para compartir con el equipo
*   **Manejo de Errores:** Continúa aunque falle la copia secundaria
*   **Reintentos Programados:** Si Google Drive no está disponible, reintenta automáticamente

### 🏗️ **Arquitectura Modular**
*   **Scripts Especializados:** Scripts independientes para generar reportes específicos (colores, feriados)
*   **Módulos Especializados:** `etl_processor`, `report_generator`, `file_delivery`, `data_validator`
*   **Configuración Unificada:** Toda la configuración centralizada en `config/unified_config.json`

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
    ```env
    # Configuración de resiliencia
    API_TIMEOUT_BASE=30
    API_MAX_RETRIES=3
    ENABLE_FALLBACK=true

    # Configuración de entrega dual
    ENABLE_DUAL_DELIVERY=true
    GDRIVE_ROOT=${USERPROFILE}/Google Drive
    GDRIVE_PROJECT_FOLDER=Gestion_360

    # Configuración de entorno
    ENVIRONMENT=development
    LOG_LEVEL=INFO
    ```

    ### Variables de Entorno Importantes

    | Variable | Descripción | Valor por Defecto |
    |----------|-------------|-------------------|
    | `API_TIMEOUT_BASE` | Timeout base para descarga API | 30 segundos |
    | `API_MAX_RETRIES` | Número máximo de reintentos | 3 |
    | `ENABLE_FALLBACK` | Usar datos anteriores si API falla | true |
    | `ENABLE_DUAL_DELIVERY` | Copiar archivos a Google Drive | true |
    | `GDRIVE_ROOT` | Ruta raíz de Google Drive | `${USERPROFILE}/Google Drive` |
    | `ENVIRONMENT` | Entorno (development/production) | development |
    | `LOG_LEVEL` | Nivel de logging | INFO |

## Uso

### Proceso Unificado con Desktop (Recomendado)
El sistema ahora incluye **automatización Desktop inteligente**:

```bash
# Proceso completo unificado con integración Desktop
python orchestrator.py --full-etl

# O usando el archivo .bat (recomendado para programación)
run_stock_process.bat
```

**Flujo Desktop Automatizado:**
1. **Usuario**: Coloca `STOCK_MODELO_COLOR.xls` en Desktop (ej: 7:00 AM)
2. **Sistema**: Ejecuta automáticamente a las 8:00 AM vía Programador de Tareas
3. **Procesamiento**: Detecta, procesa y elimina archivo automáticamente
4. **Mantenimiento**: Resto del día mantiene resultados anteriores

### Programación Desktop (Windows)
Para automatización completa:

```cmd
# Configurar Windows Task Scheduler
1. Abrir "Programador de Tareas"
2. Crear tarea básica
3. Acción: Iniciar un programa
4. Programa: C:\Windows\System32\cmd.exe
5. Argumentos: /c "C:\ruta\completa\run_stock_process.bat"
6. Programación: Diario 8:00 AM
7. Ejecutar tanto si está conectado como si no
```

### Scripts Individuales (Desarrollo)
Para desarrollo y pruebas específicas:

```bash
# ETL principal solo
python main.py

# Scripts especializados (solo cuando hay cambios)
python scripts/generate_colores_json.py   # Colores con integración Desktop
python scripts/generate_feriados_json.py  # Solo feriados

# Script de prueba para integración Desktop
python scripts/test_desktop_integration.py
```

### Lógica Inteligente del Sistema
El orquestador ejecuta procesos de manera inteligente:

- **📊 Stock (ETL Principal):** Siempre se ejecuta (datos diarios)
- **🎨 Colores (Desktop):** Detecta automáticamente archivos en Desktop y procesa una sola vez
- **📅 Feriados:** Solo cuando cambia el archivo de feriados

### Estados Desktop
El sistema maneja varios estados automáticamente:

- **🆕 Nuevo archivo**: Procesa inmediatamente y elimina
- **📅 Ya procesado**: Mantiene resultados del día
- **📁 Sin archivo**: Usa resultados anteriores si existen
- **⚠️ Error**: Registra y mantiene estado anterior

## Archivos Generados

**TODOS los archivos se generan en un solo directorio unificado:** `outputs/reports/`

### Reportes Excel
- `reporte_stock_hoy.xlsx` - Reporte principal de stock diario
- `reporte_especiales.xlsx` - Reporte de códigos especiales
- `stock_color.xlsx` - Reporte de colores por código (generado desde Desktop)
- `reporte_historico_general_VES.xlsx` - Reporte histórico VES

### Archivos JSON
- `productos_local.json` - JSON para aplicaciones web (IndexedDB)
- `stock_generales.json` - JSON para Firestore/Dialogflow
- `colores_por_codigo.json` - JSON con stock por colores agrupado (desde Desktop)
- `feriados.json` - JSON con feriados peruanos

### Archivos de Control (Desktop)
- `logs/desktop_colors_processed.json` - Control de procesamiento Desktop
- `logs/colors_data_hash.json` - Hash para detección de cambios

### Entrega Dual Inteligente
- **Archivos Originales**: Se mantienen en `outputs/reports/` (proyecto)
- **Copias Sincronizadas**: Opcional a Google Drive (`G:\My Drive\Gestion_360\360_salida`)
- **Manejo de Errores**: Si Google Drive no está disponible, continúa con archivos originales
- **Reintentos**: Si falla la copia, se reintenta automáticamente en próximas ejecuciones

## Estructura del Proyecto

```
.
├── .env.example                          # Ejemplo de variables de entorno
├── .gitignore                           # Archivos ignorados por Git
├── README.md                            # Documentación completa del sistema
├── requirements.txt                     # Dependencias del proyecto
├── DESKTOP_INTEGRATION_README.md        # Documentación específica Desktop
├── run_stock_process.bat                # 🚀 Proceso ETL completo unificado
├── orchestrator.py                      # 🏗️ Orquestador principal (con Desktop)
├── main.py                              # 📊 ETL principal (descarga y procesa)
├── config/                              # ⚙️ Configuración centralizada
│   ├── unified_config.json              # Configuración unificada
│   └── config.py                        # Configuración modular
├── modules/                             # 🔧 Módulos especializados
│   ├── etl_processor.py                 # Procesador ETL
│   ├── report_generator.py              # Generador de reportes (con Desktop)
│   ├── file_delivery.py                 # Sistema de entrega
│   └── data_validator.py                # Validador de datos
├── scripts/                             # 🐍 Scripts especializados
│   ├── run_complete_process.py          # Proceso completo
│   ├── generate_colores_json.py         # 🎨 Colores con integración Desktop
│   ├── generate_feriados_json.py        # 📅 Feriados
│   ├── test_desktop_integration.py      # 🧪 Pruebas integración Desktop
│   └── scheduler_process.py             # ⏰ Programación
├── data_sources/                        # 📥 Datos de entrada organizados
│   ├── catalogs/                        # Catálogos de productos
│   │   └── codigos_generales.xlsx       # 1,097 códigos válidos
│   └── raw_reports/                     # Reportes fuente
├── outputs/reports/                     # 🎯 TODOS LOS RESULTADOS UNIFICADOS
├── procesamiento/                       # 🔄 Archivos intermedios
├── logs/                                # 📋 Archivos de log + control Desktop
└── venv/                                # 🐍 Entorno virtual
```

## Configuración

### `config/unified_config.json` - Configuración Unificada
Archivo de configuración centralizada que controla todo el sistema:
- **Orquestador:** Configuración del sistema unificado
- **Reportes:** Definición de todos los tipos de reportes (incluyendo Desktop)
- **Entrega:** Configuración de servidores de destino
- **Directorios:** Rutas centralizadas y flexibles

### `config/config.py` - Configuración Modular
Configuración específica para módulos especializados:
- **ETL Processor:** Configuración del procesamiento de datos
- **Report Generator:** Configuración de generación de reportes (con Desktop)
- **File Delivery:** Configuración de entrega de archivos

### Configuración Desktop Específica
```python
# Archivos clave del sistema Desktop
DESKTOP_FILE = r"C:\Users\ccusi\Desktop\STOCK_MODELO_COLOR.xls"
CATALOG_FILE = "data_sources/catalogs/codigos_generales.xlsx"
PROCESSED_MARKER = "logs/desktop_colors_processed.json"
```

### Variables Importantes
*   `outputs/reports/`: **Directorio unificado** para TODOS los resultados
*   `data_sources/`: Directorio de datos de entrada
*   `logs/`: Directorio de archivos de log + control Desktop
*   `procesamiento/`: Archivos intermedios de procesamiento

## Notas Importantes

### 🚀 **Sistema Resiliente y Robusto**
*   **Alta Disponibilidad:** El sistema nunca se detiene por fallos temporales de la API
*   **Recuperación Automática:** Reintenta automáticamente sin intervención manual
*   **Fallback Inteligente:** Usa datos anteriores si la API no está disponible
*   **Detección de Cambios:** Solo procesa cuando hay datos nuevos significativos

### 📱 **Automatización Desktop Avanzada** (NUEVO)
*   **Procesamiento Automático:** Detecta archivos en Desktop sin intervención manual
*   **Lógica "Una Vez":** Procesa una sola vez por día y elimina archivo fuente
*   **Parser Inteligente:** Reconoce códigos por apóstrofe con formato robusto
*   **Filtrado Oficial:** Solo códigos presentes en catálogo de 1,097 códigos
*   **Mantenimiento Continuo:** Preserva resultados durante el día completo
*   **Control de Estados:** Maneja múltiples escenarios automáticamente

### 💾 **Gestión de Datos**
*   **Instantáneas de Stock:** La función `save_daily_stock_snapshot` toma una única instantánea del stock por día
*   **Histórico Inteligente:** Mantiene datos históricos para fallback y análisis de tendencias
*   **Validación de Integridad:** Verifica que los datos descargados sean útiles y consistentes
*   **Control Desktop:** Registra procesamiento diario para evitar duplicados

### 📤 **Entrega Dual Inteligente**
*   **Archivos Originales:** Se mantienen en `outputs/reports/` (proyecto)
*   **Copias Sincronizadas:** Opcional a Google Drive para compartir con el equipo
*   **Manejo de Errores:** Continúa aunque falle la copia secundaria
*   **Reintentos Programados:** Si Google Drive no está disponible, reintenta automáticamente

### 🏗️ **Arquitectura y Mantenimiento**
*   **Sistema Unificado:** El orquestador coordina TODOS los procesos y consolida los resultados
*   **Arquitectura Modular:** Módulos especializados permiten mantenibilidad y escalabilidad
*   **Configuración Portable:** Funciona en cualquier directorio y sistema operativo
*   **Logging Completo:** Registros detallados para monitoreo y debugging
*   **Integración Desktop:** Módulo especializado para automatización con Desktop

### 📁 **Estructura de Archivos**
*   **Archivos Ignorados:** Los directorios `data_sources/`, `procesamiento/`, `outputs/`, `logs/` están en `.gitignore`
*   **Template Incluido:** `.env.example` para configuración fácil en nuevos entornos
*   **Documentación Completa:** README actualizado con todas las características nuevas
*   **Documentación Desktop:** `DESKTOP_INTEGRATION_README.md` para funcionalidades específicas

### 🧪 **Pruebas y Validación**
*   **Script de Pruebas:** `test_desktop_integration.py` para validar sistema completo
*   **Logs Detallados:** Registro completo de todas las operaciones Desktop
*   **Estados Persistentes:** Control de procesamiento diario para evitar duplicados
*   **Recuperación Automática:** Manejo robusto de errores y estados inconsistentes