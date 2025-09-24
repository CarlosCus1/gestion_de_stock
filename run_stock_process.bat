@echo off
REM Script para gestion de stock con manejo inteligente de errores

echo [INFO] Iniciando proceso de gestion de stock...

REM Cambia al directorio del script
cd /d "%~dp0"

REM Ejecuta el proceso principal y captura el código de error
python orchestrator.py --full-etl >nul 2>nul
set EXIT_CODE=%errorlevel%

if %EXIT_CODE% equ 0 (
    REM Proceso exitoso - entrega dual y salida automática
    echo [SUCCESS] Proceso ETL completado exitosamente

    REM Entrega dual silenciosa
    xcopy "outputs\reports\*.xlsx" "G:\My Drive\Gestion_360\360_salida\" /Y /D /C /Q >nul 2>nul
    xcopy "outputs\reports\*.json" "G:\My Drive\Gestion_360\360_salida\" /Y /D /C /Q >nul 2>nul
    xcopy "outputs\reports\reporte_stock_hoy.xlsx" "%USERPROFILE%\Desktop\" /Y /D /C /Q >nul 2>nul

    echo [SUCCESS] Entrega dual completada - archivos distribuidos
    echo.
    echo [INFO] =================================================================
    echo [INFO] ARCHIVOS GENERADOS Y DISTRIBUIDOS:
    echo [INFO] =================================================================
    echo [INFO] 📁 outputs/reports/ (8 archivos)
    echo [INFO] 📤 G:\My Drive\Gestion_360\360_salida\ (copias completas)
    echo [INFO] 🖥️  %USERPROFILE%\Desktop\ (reporte principal)
    echo [INFO] =================================================================
    echo.
    REM Salida automática en caso de éxito
    goto :eof

) else (
    REM Error en el proceso - mostrar mensaje y esperar
    echo.
    echo [ERROR] =================================================================
    echo [ERROR] El proceso ETL finalizo con errores (codigo: %EXIT_CODE%)
    echo [ERROR] =================================================================
    echo.
    echo [INFO] Posibles causas:
    echo [INFO] - Error de conectividad a la API de Cipsa
    echo [INFO] - Archivos de configuracion faltantes
    echo [INFO] - Problemas con archivos de datos fuente
    echo.
    echo [INFO] Revisa los logs en procesamiento/logs/ para mas detalles
    echo.
    pause
    exit /b %EXIT_CODE%
)



