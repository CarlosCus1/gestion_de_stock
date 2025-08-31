import os
import pandas as pd
import logging
import requests
from io import BytesIO
from typing import List, Optional, Tuple, Dict

from config import settings

def validate_file_exists(filepath: str, description: str) -> bool:
    """Verifica si un archivo existe y loguea el resultado."""
    if not os.path.exists(filepath):
        logging.error(f"{description} no encontrado: {filepath}")
        return False
    logging.info(f"{description} encontrado: {filepath}")
    return True

def download_and_parse_rept_stock() -> Optional[pd.DataFrame]:
    """Descarga y procesa el reporte de stock desde la API."""
    logging.info("Descargando REPT_STOCK...")
    try:
        response = requests.get(settings.STOCK_API_URL, timeout=120)
        response.raise_for_status()
        with BytesIO(response.content) as f:
            df_raw = pd.read_excel(f, skiprows=10, dtype=str)

        df = df_raw.iloc[:, [1, 2, 9, 13, 16, 18]].copy()
        df.columns = ["ARTÍCULO", "NOMBRE_ARTICULO", "ALMACEN", "STOCK TOTAL", "PREDESPACHO", "DISPONIBLE"]
        df.rename(columns=settings.REPT_STOCK_COLS_MAP, inplace=True)
        
        df.dropna(subset=["codigo", "almacen"], inplace=True)
        df["codigo"] = df["codigo"].astype(str).str.strip()

        numeric_cols = ["stock_total", "predespacho", "disponible"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df_pivot = df.pivot_table(
            index="codigo",
            columns="almacen",
            values=numeric_cols,
            aggfunc="first",
            fill_value=0
        )
        df_pivot.columns = [f"{alm}_{tipo.replace(' ', '_')}" for tipo, alm in df_pivot.columns]
        df_pivot.reset_index(inplace=True)
        df_pivot['codigo'] = df_pivot['codigo'].astype(str).str.strip() # Ensure codigo remains string after pivot
        # Remove all spaces
        df_pivot['codigo'] = df_pivot['codigo'].str.replace(' ', '', regex=False)

        ves_disponible_col = next((col for col in df_pivot.columns if 'VES' in col.upper() and 'disponible' in col.lower()), None)
        if ves_disponible_col:
            df_pivot[settings.STANDARD_COLUMN_NAMES['stock_referencial']] = df_pivot[ves_disponible_col].astype(int)
        else:
            df_pivot[settings.STANDARD_COLUMN_NAMES['stock_referencial']] = 0
            logging.warning("No se encontró columna con stock de VES, usando 0 como stock referencial")

        logging.info(f"REPT_STOCK procesado: {len(df_pivot)} productos.")
        return df_pivot
    except Exception as e:
        logging.error(f"Error descargando REPT_STOCK: {e}")
        return None

def load_catalogs_and_lines() -> Tuple[List[str], pd.DataFrame, pd.DataFrame]:
    """Carga las plantillas manuales de Excel."""
    logging.info("Cargando plantillas manuales. Asegúrese que los encabezados son: 'codigo', 'nombre', 'linea', 'orden', 'u_por_caja'")
    try:
        required_files = [
            (settings.INPUT_LINES_TO_PROCESS_EXCEL, "Archivo de líneas a procesar"),
            (settings.INPUT_GENERALES_EXCEL, "Catálogo de códigos generales"),
            (settings.INPUT_ESPECIALES_EXCEL, "Catálogo de códigos especiales")
        ]
        for filepath, description in required_files:
            if not validate_file_exists(filepath, description):
                return [], pd.DataFrame(), pd.DataFrame()

        df_lineas = pd.read_excel(settings.INPUT_LINES_TO_PROCESS_EXCEL)
        df_lineas.rename(columns=settings.MANUAL_COLS_MAP, inplace=True)
        lineas = df_lineas["linea"].astype(str).str.strip().tolist()
        if 'ESPECIALES' in lineas:
            lineas.remove('ESPECIALES')

        df_generales = pd.read_excel(settings.INPUT_GENERALES_EXCEL, dtype={'codigo': str})
        df_generales.rename(columns=settings.MANUAL_COLS_MAP, inplace=True)
        
        df_especiales = pd.read_excel(settings.INPUT_ESPECIALES_EXCEL, dtype={'codigo': str})
        df_especiales.rename(columns=settings.MANUAL_COLS_MAP, inplace=True)

        logging.info(f"Cargadas {len(lineas)} líneas a procesar.")
        logging.info(f"Catálogo generales: {len(df_generales)} códigos.")
        logging.info(f"Catálogo especiales: {len(df_especiales)} códigos.")

        return lineas, df_generales, df_especiales
    except Exception as e:
        logging.error(f"Error cargando catálogos y líneas: {e}")
        return [], pd.DataFrame(), pd.DataFrame()

def load_base_total() -> Optional[pd.DataFrame]:
    """Carga el archivo base_total.xls del ERP."""
    if not validate_file_exists(settings.INPUT_BASE_TOTAL, "Base total"):
        return None
    try:
        df_base = pd.read_excel(settings.INPUT_BASE_TOTAL, engine='xlrd', dtype={'codigo': str})
        df_base.columns = df_base.columns.str.strip()
        
        cols_to_drop = ['FLG_INACTIVO', 'FLG_DESCONTINUADO']
        df_base.drop(columns=cols_to_drop, inplace=True, errors='ignore')

        df_base.rename(columns=settings.BASE_TOTAL_COLS_MAP, inplace=True)

        required_columns = ['codigo', 'nombre', 'linea']
        if not all(col in df_base.columns for col in required_columns):
            logging.error(f"Columnas requeridas {required_columns} faltantes en base_total.")
            return None

        df_base['codigo'] = df_base['codigo'].astype(str).str.strip()
        # Remove all spaces
        df_base['codigo'] = df_base['codigo'].str.replace(' ', '', regex=False)
        df_base['linea'] = df_base['linea'].astype(str).str.strip()

        for col in ['ean', 'ean_14']:
            if col in df_base.columns:
                df_base[col] = df_base[col].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                # Remove all spaces
                df_base[col] = df_base[col].str.replace(' ', '', regex=False)

        logging.info(f"Base total procesada: {len(df_base)} productos.")
        return df_base
    except Exception as e:
        logging.error(f"Error procesando base_total.xls: {e}")
        return None



def merge_catalogs(df_generales: pd.DataFrame, df_especiales: pd.DataFrame) -> pd.DataFrame:
    """Fusiona los catálogos de códigos generales y especiales."""
    try:
        df_generales['codigo'] = df_generales['codigo'].astype(str).str.strip()
        df_especiales['codigo'] = df_especiales['codigo'].astype(str).str.strip()

        catalogo_df = pd.concat([df_generales, df_especiales], ignore_index=True, sort=False)
        catalogo_df = catalogo_df.fillna('')

        if 'u_por_caja' in catalogo_df.columns:
            catalogo_df['u_por_caja'] = pd.to_numeric(catalogo_df['u_por_caja'], errors='coerce').fillna(1).astype(int)
        else:
            catalogo_df['u_por_caja'] = 1

        if 'orden' in catalogo_df.columns:
            catalogo_df['orden'] = pd.to_numeric(catalogo_df['orden'], errors='coerce').fillna(0).astype(int)
        else:
            catalogo_df['orden'] = 0

        logging.info(f"Catálogo fusionado: {len(catalogo_df)} códigos")
        return catalogo_df
    except Exception as e:
        logging.error(f"Error fusionando catálogos: {e}")
        return pd.DataFrame({'codigo': [], 'u_por_caja': [], 'orden': []})