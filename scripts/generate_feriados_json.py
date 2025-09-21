#!/usr/bin/env python3
"""
Script para generar feriados.json desde feriados.xlsx
Lee el archivo Excel de feriados y genera el JSON correspondiente.
"""

import pandas as pd
import json
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Importar configuración centralizada
try:
    from config import settings
except ImportError:
    # Fallback: intentar importar directamente
    import importlib.util
    config_path = os.path.join(project_root, 'config', 'config.py')
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    settings = config_module.settings

def generate_feriados_json():
    """
    Genera el archivo feriados.json desde feriados.xlsx
    """
    try:
        # Rutas de archivos (usando rutas directas por compatibilidad)
        input_file = "data_sources/catalogs/feriados.xlsx"
        output_file = "outputs/reports/feriados.json"

        # Verificar que existe el archivo de entrada
        if not os.path.exists(input_file):
            print(f"[ERROR] No se encuentra el archivo {input_file}")
            return False

        # Crear directorio de salida si no existe
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Leer el archivo Excel
        print("[INFO] Leyendo archivo de feriados...")
        df = pd.read_excel(input_file, sheet_name='Hoja1')

        # Verificar que las columnas existen
        if 'fecha' not in df.columns or 'nombre' not in df.columns:
            print("[ERROR] El archivo Excel debe tener las columnas 'fecha' y 'nombre'")
            return False

        # Convertir fechas a string en formato MM/DD
        print("[INFO] Procesando fechas...")
        feriados_dict = {}
        for _, row in df.iterrows():
            fecha = row['fecha']
            nombre = row['nombre']

            # Convertir fecha a string MM/DD
            if pd.notna(fecha):
                if hasattr(fecha, 'strftime'):
                    # Es un objeto datetime
                    fecha_str = fecha.strftime('%m/%d')
                else:
                    # Es un string, intentar parsear
                    try:
                        fecha_dt = pd.to_datetime(fecha)
                        fecha_str = fecha_dt.strftime('%m/%d')
                    except:
                        print(f"[WARNING] No se pudo procesar la fecha: {fecha}")
                        continue

                feriados_dict[fecha_str] = nombre

        # Guardar como JSON
        print("[INFO] Guardando feriados.json...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(feriados_dict, f, ensure_ascii=False, indent=2)

        print(f"[SUCCESS] Feriados.json generado exitosamente en {output_file}")
        print(f"[INFO] Total de feriados procesados: {len(feriados_dict)}")

        return True

    except Exception as e:
        print(f"[ERROR] Error generando feriados.json: {str(e)}")
        return False

if __name__ == "__main__":
    print("[INFO] Iniciando generacion de feriados.json...")
    success = generate_feriados_json()
    if success:
        print("[SUCCESS] Proceso completado exitosamente")
    else:
        print("[ERROR] Proceso fallo")
        exit(1)