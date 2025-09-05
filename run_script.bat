@echo off
set "PROJECT_DIR=c:\Users\ccusi\Documents\Proyect_Coder\gestion_de_stock"

REM Activa el entorno virtual
call "%PROJECT_DIR%\venv\Scripts\activate.bat"

REM Cambia al directorio del proyecto y ejecuta el script de Python
cd /d "%PROJECT_DIR%"
python main.py

REM Si el código de salida (%ERRORLEVEL%) no es 0, muestra un mensaje de error.
if %ERRORLEVEL% neq 0 (
    mshta "javascript:alert('Ocurrió un error al ejecutar la actualización de stock.');close();"
)

REM Desactiva el entorno virtual
call "%PROJECT_DIR%\venv\Scripts\deactivate.bat"
