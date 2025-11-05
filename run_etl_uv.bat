@echo off
:: Script de ejecucion en segundo plano - Sistema de Gestion de Stock
:: Version UV + Python 3.13 - Sin pausas, auto-cierre

cd /d "%~dp0"

:: Crear log de ejecucion con timestamp
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set mydate=%%c%%b%%a
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a%%b
set logfile=logs\etl_background_%mydate%_%mytime%.log

:: Crear directorio de logs si no existe
if not exist "logs" mkdir logs

:: Verificar UV y ejecutar en segundo plano
uv --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [%date% %time%] UV disponible - Ejecutando ETL en segundo plano >> "%logfile%"
    start /B uv run --python 3.13 orchestrator.py --full-etl >> "%logfile%" 2>&1
    echo [%date% %time%] Proceso ETL iniciado en background - Log: %logfile% >> "%logfile%"
) else (
    :: Fallback a Python directo si UV no disponible
    echo [%date% %time%] UV no disponible, usando Python directo >> "%logfile%"
    py -3.13 --version >nul 2>&1
    if %errorlevel% equ 0 (
        start /B py -3.13 orchestrator.py --full-etl >> "%logfile%" 2>&1
        echo [%date% %time%] Proceso Python iniciado en background - Log: %logfile% >> "%logfile%"
    ) else (
        start /B python orchestrator.py --full-etl >> "%logfile%" 2>&1
        echo [%date% %time%] Proceso Python basico iniciado en background - Log: %logfile% >> "%logfile%"
    )
)

:: Auto-cierre del script (no pause)
exit /b 0