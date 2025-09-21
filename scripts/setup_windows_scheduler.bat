@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 🚀 CONFIGURANDO SCHEDULER ETL AUTOMÁTICO
echo ========================================
echo.

echo 📅 Configuración:
echo    - Frecuencia: Cada hora
echo    - Horario: 7:00 - 23:00 (Lunes-Sábado)
echo    - Script: scheduler_process.py
echo.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
set "PYTHON_PATH=%SCRIPT_DIR%..\venv\Scripts\python.exe"

if not exist "%PYTHON_PATH%" (
    echo ❌ Error: No se encontró Python en la ruta esperada
    echo 📍 Ruta buscada: %PYTHON_PATH%
    echo.
    echo 💡 Solución: Asegúrate de tener Python instalado y activado
    pause
    exit /b 1
)

echo ✅ Python encontrado en: %PYTHON_PATH%
echo.

echo 🔧 Creando tarea programada...

schtasks /create /tn "ETL_StockDataMatrix_Scheduler" /tr "\"%PYTHON_PATH%\" \"%PROJECT_DIR%\scripts\scheduler_process.py\"" /sc hourly /mo 1 /st 07:00 /et 23:00 /d MON,TUE,WED,THU,FRI,SAT /f /rl highest >nul 2>&1

if %errorlevel% neq 0 (
    echo ❌ Error al crear la tarea programada
    echo.
    echo 💡 Solución: Ejecuta como Administrador
    echo    - Clic derecho en el archivo .bat
    echo    - "Ejecutar como administrador"
    pause
    exit /b 1
)

echo ✅ Tarea programada creada exitosamente!
echo.

echo 📊 Verificando tarea creada...
schtasks /query /tn "ETL_StockDataMatrix_Scheduler" | findstr /c:"ETL_StockDataMatrix_Scheduler" >nul

if %errorlevel% equ 0 (
    echo ✅ Tarea verificada correctamente
) else (
    echo ❌ Error al verificar la tarea
    pause
    exit /b 1
)

echo.
echo ========================================
echo 📋 RESUMEN DE CONFIGURACIÓN
echo ========================================
echo.
echo 🎯 Tarea: ETL_StockDataMatrix_Scheduler
echo 📅 Días: Lunes a Sábado
echo ⏰ Horario: 7:00 - 23:00 (cada hora)
echo 📁 Ubicación: %PROJECT_DIR%
echo 🐍 Python: %PYTHON_PATH%
echo.
echo ========================================
echo 📝 PRÓXIMOS PASOS
echo ========================================
echo.
echo 1. ✅ La tarea se ejecutará automáticamente cada hora
echo 2. 📧 Revisa los logs en: logs/scheduler_YYYYMMDD.log
echo 3. 📊 Estadísticas en: logs/execution_stats.json
echo 4. 🛠️ Para modificar: schtasks /change /tn "ETL_StockDataMatrix_Scheduler"
echo 5. 🗑️ Para eliminar: schtasks /delete /tn "ETL_StockDataMatrix_Scheduler"
echo.
echo ========================================
echo 🎉 CONFIGURACIÓN COMPLETADA
echo ========================================

pause