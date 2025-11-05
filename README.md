# Sistema de Gestión de Stock

**Sistema ETL Unificado y Resiliente** que automatiza la descarga, procesamiento y generación de informes de stock con **alta disponibilidad**, **recuperación automática** e **integración inteligente con Desktop**. Genera TODOS los reportes en un solo directorio centralizado (`outputs/reports/`), con entrega dual opcional.

## ✨ Características Principales

### 🚀 **Resiliencia y Recuperación**
- **Descarga API con reintentos**: Hasta 3 reintentos con timeout progresivo
- **Fallback automático**: Usa datos anteriores si la API falla
- **Detección de cambios**: Solo procesa cuando hay datos nuevos
- **Recuperación automática**: Se reintenta sin intervención manual

### 📱 **Automatización Desktop Inteligente**
- **Procesamiento automático**: Detecta archivos en Desktop automáticamente
- **Lógica "una vez y elimina"**: Procesa archivo una sola vez y elimina TODOS los archivos del Desktop
- **Limpieza completa**: Elimina `STOCK_MODELO_COLOR.xls` y `log.txt` del Desktop
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

## 🔧 Configuración del Entorno

### Requisitos Previos
- **Python 3.13.9+** (recomendado)
- **UV** - Gestor de paquetes moderno y ultra rápido

### Instalación de UV
```bash
# Instalar UV (gestor de paquetes moderno y ultra rápido)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verificar instalación
uv --version
```

### Configuración del Proyecto
1. **Clonar el Repositorio:**
    ```bash
    git clone https://github.com/tu_usuario/gestion_de_stock.git
    cd gestion_de_stock
    ```

2. **Instalar dependencias con UV:**
    ```bash
    # Instalación automática de dependencias
    uv run --frozen python --version
    
    # O usar el script optimizado
    run_etl_uv.bat
    ```

3. **Configuración de Variables de Entorno:**
    Crea un archivo `.env` en la raíz del proyecto basado en `.env.example`.

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

## 🚀 Uso

### Proceso Unificado (Recomendado)
El sistema incluye **automatización inteligente**:

```bash
# Proceso completo unificado con UV (UNICO SCRIPT FUNCIONAL)
run_etl_uv.bat

# O comando directo
uv run python orchestrator.py --full-etl
```

**Flujo Automatizado:**
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
5. Argumentos: /c "C:\ruta\completa\run_etl_uv.bat"
6. Programación: Diario 8:00 AM
7. Ejecutar tanto si está conectado como si no
```

### Scripts Individuales (Desarrollo)
Para desarrollo y pruebas específicas:

```bash
# ETL principal solo
uv run python main.py

# Scripts especializados (solo cuando hay cambios)
uv run python scripts/generate_colores_json.py   # Colores con integración Desktop
uv run python scripts/generate_feriados_json.py  # Solo feriados

# Orquestador - comandos específicos
uv run python orchestrator.py --help             # Ver ayuda
uv run python orchestrator.py --list-reports     # Listar reportes disponibles
uv run python orchestrator.py --list-servers     # Listar servidores configurados
```

### Lógica Inteligente del Sistema
El orquestador ejecuta procesos de manera inteligente:

- **📊 Stock (ETL Principal):** Siempre se ejecuta (datos diarios)
- **🎨 Colores (Desktop):** Detecta automáticamente archivos en Desktop y procesa una sola vez
- **📅 Feriados:** Solo cuando cambia el archivo de feriados

## 📊 Archivos Generados

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

## 📁 Estructura del Proyecto

```
.
├── .env.example                          # Ejemplo de variables de entorno
├── .gitignore                           # Archivos ignorados por Git
├── README.md                            # Documentación completa del sistema
├── requirements.txt                     # Dependencias del proyecto
├── pyproject.toml                       # Configuración UV
├── uv.lock                              # Lock file de UV
├── run_etl_uv.bat                       # ⚡ Script optimizado con UV (ÚNICO FUNCIONAL)
├── orchestrator.py                      # 🏗️ Orquestador principal
├── main.py                              # 📊 ETL principal
├── config/                              # ⚙️ Configuración centralizada
│   ├── config.py                        # Configuración modular
│   └── unified_config.json              # Configuración unificada
├── modules/                             # 🔧 Módulos especializados
│   ├── etl_processor.py                 # Procesador ETL
│   ├── report_generator.py              # Generador de reportes
│   ├── file_delivery.py                 # Sistema de entrega
│   └── data_validator.py                # Validador de datos
├── scripts/                             # 🐍 Scripts especializados
│   ├── run_complete_process.py          # Proceso completo
│   ├── generate_colores_json.py         # 🎨 Colores con integración Desktop
│   ├── generate_feriados_json.py        # 📅 Feriados
│   ├── test_desktop_integration.py      # 🧪 Pruebas integración Desktop
│   ├── scheduler_process.py             # ⏰ Programación
│   ├── drive_centric_processor.py       # 🌐 Procesador centrado en Drive
│   └── local_processor_simple.py        # 💻 Procesador local simple
├── data_sources/                        # 📥 Datos de entrada organizados
│   ├── catalogs/                        # Catálogos de productos
│   │   └── codigos_generales.xlsx       # 1,097 códigos válidos
│   └── raw_reports/                     # Reportes fuente
├── outputs/reports/                     # 🎯 TODOS LOS RESULTADOS UNIFICADOS
├── procesamiento/                       # 🔄 Archivos intermedios
├── data_schemas/                        # 📋 Esquemas de datos
│   └── pydantic_models/
│       └── schemas.py                   # Modelos Pydantic
└── logs/                                # 📋 Archivos de log + control Desktop
```

## ⚙️ Configuración

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
* `outputs/reports/`: **Directorio unificado** para TODOS los resultados
* `data_sources/`: Directorio de datos de entrada
* `logs/`: Directorio de archivos de log + control Desktop
* `procesamiento/`: Archivos intermedios de procesamiento

## 📝 Notas Importantes

### 🚀 **Sistema Resiliente y Robusto**
* **Alta Disponibilidad:** El sistema nunca se detiene por fallos temporales de la API
* **Recuperación Automática:** Reintenta automáticamente sin intervención manual
* **Fallback Inteligente:** Usa datos anteriores si la API no está disponible
* **Detección de Cambios:** Solo procesa cuando hay datos nuevos significativos

### 📱 **Automatización Desktop Avanzada**
* **Procesamiento Automático:** Detecta archivos en Desktop sin intervención manual
* **Lógica "Una Vez":** Procesa una sola vez por día y elimina archivo fuente
* **Parser Inteligente:** Reconoce códigos por apóstrofe con formato robusto
* **Filtrado Oficial:** Solo códigos presentes en catálogo de 1,097 códigos
* **Mantenimiento Continuo:** Preserva resultados durante el día completo
* **Control de Estados:** Maneja múltiples escenarios automáticamente

### 💾 **Gestión de Datos**
* **Instantáneas de Stock:** La función `save_daily_stock_snapshot` toma una única instantánea del stock por día
* **Histórico Inteligente:** Mantiene datos históricos para fallback y análisis de tendencias
* **Validación de Integridad:** Verifica que los datos descargados sean útiles y consistentes
* **Control Desktop:** Registra procesamiento diario para evitar duplicados

### 📤 **Entrega Dual Inteligente**
* **Archivos Originales:** Se mantienen en `outputs/reports/` (proyecto)
* **Copias Sincronizadas:** Opcional a Google Drive para compartir con el equipo
* **Manejo de Errores:** Continúa aunque falle la copia secundaria
* **Reintentos Programados:** Si Google Drive no está disponible, reintenta automáticamente

### 🏗️ **Arquitectura y Mantenimiento**
* **Sistema Unificado:** El orquestador coordina TODOS los procesos y consolida los resultados
* **Arquitectura Modular:** Módulos especializados permiten mantenibilidad y escalabilidad
* **Configuración Portable:** Funciona en cualquier directorio y sistema operativo
* **Logging Completo:** Registros detallados para monitoreo y debugging
* **Integración Desktop:** Módulo especializado para automatización con Desktop

### 🔧 **Gestión de Paquetes con UV**
* **UV es 10-100x más rápido** que pip/pipenv/Poetry
* **Resolución instantánea** de dependencias
* **Gestión automática** de entornos virtuales
* **Fallback automático** a Python si UV no está disponible
* **Lock files robustos** con uv.lock

### 📁 **Estructura de Archivos**
* **Archivos Ignorados:** Los directorios `data_sources/`, `procesamiento/`, `outputs/`, `logs/` están en `.gitignore`
* **Template Incluido:** `.env.example` para configuración fácil en nuevos entornos
* **Documentación Completa:** README actualizado con todas las características
* **Código Limpio:** Archivos obsoletos y códigos muertos eliminados

### 🧪 **Pruebas y Validación**
* **Script de Pruebas:** `scripts/test_desktop_integration.py` para validar sistema completo
* **Logs Detallados:** Registro completo de todas las operaciones Desktop
* **Estados Persistentes:** Control de procesamiento diario para evitar duplicados
* **Recuperación Automática:** Manejo robusto de errores y estados inconsistentes

## 🆘 Solución de Problemas

### Problemas Comunes
1. **Error de dependencias:** Usar `run_etl_uv.bat` para instalación automática
2. **Desktop no detectado:** Verificar que el archivo esté en la ruta correcta
3. **Google Drive no disponible:** El sistema continúa sin copiar automáticamente

### Logs y Diagnóstico
- **Logs principales:** `logs/orchestrator_YYYYMMDD_HHMMSS.log`
- **Control Desktop:** `logs/desktop_colors_processed.json`
- **Verificación rápida:** `uv run python orchestrator.py --list-reports`

---

**✅ Sistema Limpio y Optimizado - Listo para Producción**