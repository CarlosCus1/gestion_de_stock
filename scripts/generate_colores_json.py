#!/usr/bin/env python3
"""
Script para generar stock_color.xlsx y colores_por_codigo.json desde STOCK_MODELO_COLOR.xls
Procesa el archivo HTML de stock por colores y genera los archivos correspondientes.
"""

import pandas as pd
import json
import os
import re
import logging
import sys

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

# Configurar logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def setup_logging():
    """Configura el sistema de logging."""
    return logger

def read_excel_file(file_path):
    """
    Lee el archivo Excel y extrae los datos.
    """
    try:
        # Intentar leer con diferentes configuraciones
        df = pd.read_excel(file_path, header=None)
        return df
    except Exception as e:
        logger.error(f"[ERROR] Error leyendo archivo Excel: {e}")
        raise

def load_codigos_generales():
    """
    Carga los códigos generales válidos desde codigos_generales.xlsx
    """
    try:
        codigos_file = "data_sources/catalogs/codigos_generales.xlsx"
        if not os.path.exists(codigos_file):
            logger.warning(f"[WARNING] No se encontró {codigos_file}, procesando todos los códigos")
            return set()

        df_codigos = pd.read_excel(codigos_file)
        codigos_validos = set()

        # Extraer códigos no vacíos y normalizarlos
        for _, row in df_codigos.iterrows():
            codigo = str(row.get('codigo', '')).strip()
            if codigo and codigo != 'nan' and not pd.isna(row.get('codigo')):
                # Normalizar: quitar comillas, espacios y convertir a string
                codigo_normalizado = codigo.strip("'\" \t\n\r").strip()
                if codigo_normalizado:
                    codigos_validos.add(codigo_normalizado)

        logger.info(f"[SUCCESS] Cargados {len(codigos_validos)} códigos válidos")
        return codigos_validos

    except Exception as e:
        logger.error(f"[ERROR] Error cargando códigos generales: {e}")
        return set()

def generate_colores_files():
    """
    Genera stock_color.xlsx y colores_por_codigo.json desde STOCK_MODELO_COLOR.xls
    """
    logger = setup_logging()

    try:
        # Rutas de archivos (usando rutas directas por compatibilidad)
        input_file = "data_sources/raw_reports/STOCK_MODELO_COLOR.xls"
        output_xlsx = "outputs/reports/stock_color.xlsx"
        output_json = "outputs/reports/colores_por_codigo.json"

        # Verificar que existe el archivo de entrada
        if not os.path.exists(input_file):
            logger.error(f"[ERROR] No se encuentra el archivo {input_file}")
            return False

        # Crear directorios de salida si no existen
        os.makedirs(os.path.dirname(output_xlsx), exist_ok=True)
        # El JSON ahora va en la misma carpeta que el Excel, no necesita directorio separado

        # Cargar códigos válidos desde codigos_generales.xlsx
        logger.info("[INFO] Cargando códigos generales válidos...")
        codigos_validos = load_codigos_generales()

        # Leer el archivo Excel
        logger.info("[INFO] Leyendo archivo STOCK_MODELO_COLOR.xls...")
        df = read_excel_file(input_file)

        # Headers basados en la estructura del archivo
        headers = ['grupo', 'tipo', 'familia', 'codigo', 'descripcion', 'modelo', 'color', 'unidades']

        # Convertir DataFrame a lista de listas
        rows = df.values.tolist()
        logger.info(f"[SUCCESS] Datos extraidos: {len(rows)} filas, {len(df.columns)} columnas")

        if not rows:
            logger.error("[ERROR] No se encontraron datos en la tabla")
            return False

        # Limpiar datos
        logger.info("[INFO] Limpiando datos...")

        # Usar solo las columnas que necesitamos
        if len(df.columns) >= 8:
            df_clean = df.iloc[:, :8].copy()
            df_clean.columns = headers
        else:
            logger.error(f"[ERROR] El archivo no tiene suficientes columnas. Encontradas: {len(df.columns)}")
            return False

        # Rellenar valores faltantes en 'codigo' y 'descripcion' para manejar celdas combinadas
        logger.info("[INFO] Rellenando códigos y descripciones para agrupar colores...")
        df_clean['codigo'] = df_clean['codigo'].replace('', pd.NA).ffill()
        df_clean['descripcion'] = df_clean['descripcion'].replace('', pd.NA).ffill()

        # Convertir unidades a numérico
        if 'unidades' in df.columns:
            df['unidades'] = pd.to_numeric(df['unidades'], errors='coerce').fillna(0).astype(int)

        # Limpiar códigos (quitar comillas simples)
        if 'codigo' in df.columns:
            df['codigo'] = df['codigo'].str.replace("'", "").str.strip()

        # Generar stock_color.xlsx con códigos repetidos por color
        logger.info("[INFO] Generando stock_color.xlsx con códigos repetidos...")

        # Crear DataFrame con códigos repetidos (cada código-color en fila separada)
        rows_data = []

        for _, row in df_clean.iterrows():
            codigo = str(row.get('codigo', '')).strip()
            if not codigo or codigo.lower() == 'codigo':  # Saltar headers
                continue

            # Normalizar código para comparación
            codigo_normalizado = codigo.strip("'\" \t\n\r").strip()

            # Solo procesar códigos válidos
            if codigos_validos and codigo_normalizado not in codigos_validos:
                continue

            descripcion = str(row.get('descripcion', '')).strip()
            color = str(row.get('color', '')).strip()
            unidades_val = row.get('unidades', 0)

            # Verificar si unidades es un número válido
            try:
                if pd.isna(unidades_val):
                    unidades = 0
                else:
                    unidades = float(unidades_val)
                    if pd.isna(unidades):
                        unidades = 0
                    else:
                        unidades = int(unidades)
            except (ValueError, TypeError):
                continue

            # Agregar fila al DataFrame (cada código-color es una fila separada)
            rows_data.append({
                'codigo': codigo_normalizado,
                'descripcion': descripcion,
                'color': color,
                'unidades': unidades
            })

        # Crear DataFrame final
        df_final = pd.DataFrame(rows_data)

        # Verificar que tenemos códigos repetidos
        if len(df_final) > 0:
            codigos_repetidos = df_final['codigo'].value_counts()
            max_repeticiones = codigos_repetidos.max()
            logger.info(f"[INFO] Código más repetido aparece {max_repeticiones} veces")

        with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
            # Hoja principal con todos los datos
            df_final.to_excel(writer, sheet_name='Colores', index=False)

            # Configurar formato
            workbook = writer.book
            worksheet = writer.sheets['Colores']

            # Ajustar ancho de columnas
            column_widths = {
                'codigo': 12,
                'descripcion': 50,
                'color': 20,
                'unidades': 10
            }

            for i, col in enumerate(df_final.columns):
                width = column_widths.get(col, 15)
                worksheet.set_column(i, i, width)

            # Agregar formato de tabla
            (max_row, max_col) = df_final.shape
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': [{'header': col} for col in df_final.columns],
                'style': 'Table Style Medium 9',
                'name': 'StockColores'
            })

        logger.info(f"[SUCCESS] stock_color.xlsx generado en {output_xlsx}")

        # Generar colores_por_codigo.json
        logger.info("[INFO] Generando colores_por_codigo.json...")

        # Agrupar por código (solo códigos válidos)
        colores_por_codigo = {}
        codigos_procesados = 0
        codigos_filtrados = 0

        for _, row in df_final.iterrows():
            codigo = str(row.get('codigo', '')).strip()
            if not codigo or codigo.lower() == 'codigo':  # Saltar headers
                continue

            # Normalizar código para comparación
            codigo_normalizado = codigo.strip("'\" \t\n\r").strip()

            # Solo procesar códigos válidos
            if codigos_validos and codigo_normalizado not in codigos_validos:
                codigos_filtrados += 1
                continue

            descripcion = str(row.get('descripcion', '')).strip()
            color = str(row.get('color', '')).strip()
            unidades_val = row.get('unidades', 0)

            # Verificar si unidades es un número válido
            try:
                if pd.isna(unidades_val):
                    unidades = 0
                else:
                    # Intentar convertir a número
                    unidades = float(unidades_val)
                    if pd.isna(unidades):
                        unidades = 0
                    else:
                        unidades = int(unidades)
            except (ValueError, TypeError):
                # Si no se puede convertir, saltar esta fila
                continue

            if codigo_normalizado not in colores_por_codigo:
                colores_por_codigo[codigo_normalizado] = {
                    'descripcion': descripcion,
                    'colores': []
                }

            colores_por_codigo[codigo_normalizado]['colores'].append({
                'color': color,
                'unidades': unidades
            })
            codigos_procesados += 1

        logger.info(f"[INFO] Códigos procesados: {codigos_procesados}, filtrados: {codigos_filtrados}")

        # Guardar JSON
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(colores_por_codigo, f, ensure_ascii=False, indent=2)

        logger.info(f"[SUCCESS] colores_por_codigo.json generado en {output_json}")
        logger.info(f"[INFO] Total de codigos procesados: {len(colores_por_codigo)}")

        return True

    except Exception as e:
        logger.error(f"[ERROR] Error generando archivos de colores: {str(e)}")
        return False

if __name__ == "__main__":
    logger = setup_logging()
    logger.info("[INFO] Iniciando generacion de archivos de colores...")
    success = generate_colores_files()
    if success:
        logger.info("[SUCCESS] Proceso completado exitosamente")
    else:
        logger.error("[ERROR] Proceso fallo")
        exit(1)