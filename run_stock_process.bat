@echo off
REM ================================================
REM Sistema de Gestión de Stock - Proceso Completo
REM ================================================
REM Este archivo ejecuta todo el proceso ETL de stock
REM Genera todos los reportes en outputs/reports/
REM
REM Uso: double-click o desde scheduler
REM ================================================

echo ================================================
echo Sistema de Gestión de Stock - Proceso Completo
echo ================================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python no está instalado
    echo.
    echo Por favor instala Python desde https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

REM Verificar si existe el directorio del proyecto
if not exist "scripts" (
    echo ❌ ERROR: No se encuentra el directorio 'scripts'
    echo.
    echo Este archivo debe estar en la raíz del proyecto
    echo.
    pause
    exit /b 1
)

echo ✅ Directorio del proyecto: %cd%
echo.

REM Verificar si existe requirements.txt
if exist "requirements.txt" (
    echo 📦 Verificando dependencias...
    pip install -r requirements.txt >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️  ADVERTENCIA: No se pudieron instalar todas las dependencias
        echo    Continuando con las dependencias existentes...
    ) else (
        echo ✅ Dependencias verificadas
    )
) else (
    echo ⚠️  ADVERTENCIA: No se encontró requirements.txt
)

echo.
echo ================================================
echo 🚀 INICIANDO PROCESO ETL COMPLETO
echo ================================================
echo.

REM Ejecutar el proceso principal
python scripts/run_complete_process.py

REM Verificar resultado
if %errorlevel% neq 0 (
    echo.
    echo ❌ ERROR: El proceso falló
    echo.
    echo Revisa los logs para más detalles
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo ✅ PROCESO COMPLETADO EXITOSAMENTE
echo ================================================
echo.
echo 📊 Archivos generados en: outputs/reports/
echo.

REM Mostrar archivos generados
if exist "outputs\reports" (
    echo 📋 Archivos generados:
    dir /b "outputs\reports" 2>nul | findstr /v /c:"$"
) else (
    echo ⚠️  No se encontró la carpeta outputs/reports
)

echo.
echo ================================================
echo Presiona cualquier tecla para salir...
pause >nul