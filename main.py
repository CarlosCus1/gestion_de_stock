import os
import pandas as pd
import logging
from datetime import datetime, timedelta # Added timedelta
import traceback
import glob
import warnings
import shutil

# Módulos de configuración y lógica de la aplicación
from config import settings
from data_loader import (
    download_and_parse_rept_stock,
    load_catalogs_and_lines,
    load_base_total,
    merge_catalogs,
    load_previous_stock,
    load_historical_stock_snapshot # Added new import
)
from report_generator import (
    generate_historical_general_stock_report,
    generate_stock_report,
    generate_especiales_report,
    generate_productos_local_json,
    generate_stock_generales_json,
    save_daily_stock_snapshot
)

# --- CONFIGURACIÓN INICIAL ---
warnings.filterwarnings('ignore', category=pd.errors.DtypeWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Crear directorios requeridos si no existen
for directory in settings.REQUIRED_DIRS:
    os.makedirs(directory, exist_ok=True)

def setup_logging():
    """Configura el sistema de logging para el script."""
    log_filename = f"proceso_{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = os.path.join(settings.LOGS_DIR, log_filename)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler()
        ],
    )
    return logging.getLogger(__name__)

def clean_temp_files():
    """Limpia archivos temporales de ejecuciones anteriores."""
    logging.info("Iniciando limpieza de archivos temporales...")
    patterns = [
        os.path.join(settings.DATOS_DIR, "REPT_STOCK_*.xls*"),
        os.path.join(settings.TEMP_DIR, "*.tmp"),
        os.path.join(settings.TEMP_DIR, "*.json"),
        os.path.join(settings.REPORTES_DIR, "reporte_final_*_backup.xlsx")
    ]
    cleaned_count = 0
    for pattern in patterns:
        for file in glob.glob(pattern):
            try:
                os.remove(file)
                logging.debug(f"Eliminado: {file}")
                cleaned_count += 1
            except Exception as e:
                logging.warning(f"No se pudo eliminar {file}: {e}")
    logging.info(f"Limpieza completada: {cleaned_count} archivos eliminados")


# --- FLUJO PRINCIPAL DE EJECUCIÓN ---
def main():
    """Función principal que orquesta todo el proceso ETL y de reportes."""
    logger = setup_logging()
    logger.info("=== INICIANDO PROCESO COMPLETO (REFACTORIZADO) ===")

    try:
        # 1. Limpieza inicial
        clean_temp_files()

        # 2. Carga y parseo de datos fuente
        logger.info("--- PASO 1: CARGANDO DATOS ---")
        df_stock = download_and_parse_rept_stock()
        if df_stock is None: return

        lineas_a_procesar, df_generales_cat, df_especiales_cat = load_catalogs_and_lines()
        if not lineas_a_procesar: return
        
        df_base = load_base_total()
        if df_base is None: return
        
        # 3. Procesamiento y consolidación de datos
        logger.info("--- PASO 2: CONSOLIDANDO DATOS ---")
        catalogo_df = merge_catalogs(df_generales_cat, df_especiales_cat)
        
        df_base = pd.merge(df_base, catalogo_df, on='codigo', how='left')
        # Fill NaN values in 'motivo' column with empty string after merge
        if 'motivo' in df_base.columns:
            df_base['motivo'] = df_base['motivo'].fillna('')
        df_base['u_por_caja'] = df_base['u_por_caja'].fillna(1).astype(int)
        df_base['orden'] = df_base['orden'].fillna(0).astype(int)
        
        df_consolidado = pd.merge(df_base, df_stock, on='codigo', how='left')
        df_consolidado['stock_referencial'] = df_consolidado.get('stock_referencial', 0).fillna(0).astype(int)

        # Load stock_anterior and merge into df_consolidado
        stock_anterior_dict = load_previous_stock()
        if stock_anterior_dict: # Only merge if there's actual previous stock data
            df_stock_anterior = pd.DataFrame(list(stock_anterior_dict.items()), columns=['codigo', 'stock_antes'])
            df_stock_anterior['codigo'] = df_stock_anterior['codigo'].astype(str).str.strip() # Ensure consistent type and cleaning
            df_consolidado = pd.merge(df_consolidado, df_stock_anterior, on='codigo', how='left')
            df_consolidado['stock_antes'] = df_consolidado['stock_antes'].fillna(0).astype(int) # Fill NaN with 0 and convert to int

        # Load historical stock for 'stock_ayer' and 'stock_hace_una_semana'
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        one_week_ago = today - timedelta(days=7)

        stock_ayer_dict = load_historical_stock_snapshot(yesterday)
        if stock_ayer_dict:
            df_stock_ayer = pd.DataFrame(list(stock_ayer_dict.items()), columns=['codigo', 'stock_ayer'])
            df_stock_ayer['codigo'] = df_stock_ayer['codigo'].astype(str).str.strip()
            df_consolidado = pd.merge(df_consolidado, df_stock_ayer, on='codigo', how='left')
            df_consolidado['stock_ayer'] = df_consolidado['stock_ayer'].fillna(0).astype(int)

        stock_hace_una_semana_dict = load_historical_stock_snapshot(one_week_ago)
        if stock_hace_una_semana_dict:
            df_stock_hace_una_semana = pd.DataFrame(list(stock_hace_una_semana_dict.items()), columns=['codigo', 'stock_hace_una_semana'])
            df_stock_hace_una_semana['codigo'] = df_stock_hace_una_semana['codigo'].astype(str).str.strip()
            df_consolidado = pd.merge(df_consolidado, df_stock_hace_una_semana, on='codigo', how='left')
            df_consolidado['stock_hace_una_semana'] = df_consolidado['stock_hace_una_semana'].fillna(0).astype(int)

        # Asegurar columnas opcionales para los reportes
        if 'precio' not in df_consolidado.columns: df_consolidado['precio'] = 0.0
        if 'can_kg_um' not in df_consolidado.columns: df_consolidado['can_kg_um'] = ''

        df_consolidado['precio'] = pd.to_numeric(df_consolidado['precio'], errors='coerce').fillna(0.0)
        df_consolidado['can_kg_um'] = pd.to_numeric(df_consolidado['can_kg_um'], errors='coerce').fillna(0.0)
        
        # Conversión final de tipos de datos numéricos
        int_columns = ['u_por_caja', 'orden', 'stock_referencial', 'stock_ayer', 'stock_hace_una_semana'] + \
                     [col for col in df_consolidado.columns if any(k in col for k in ['_stock_total', '_disponible', '_predespacho'])]
        for col in int_columns:
            if col in df_consolidado.columns:
                df_consolidado[col] = pd.to_numeric(df_consolidado[col], errors='coerce').fillna(0).astype('int64')
        
        # Guardar el snapshot consolidado, la "fuente de la verdad" para los reportes
        df_consolidado.drop_duplicates(subset=['codigo'], inplace=True) # Remove duplicate codes
        df_consolidado.drop(columns=['motivo'], errors='ignore').to_excel(settings.DATA_STOCK_COMPLETO_FILE, index=False)
        logger.info(f"{settings.DATA_STOCK_COMPLETO_FILE} generado.")
        
        # 5. Guardar estado para la próxima ejecución (snapshot del inicio del día)
        save_daily_stock_snapshot(df_consolidado)

        # 4. Generación de todos los reportes
        logger.info("--- PASO 3: GENERANDO REPORTES ---")
        
        # Preparar subconjuntos de datos para ciertos reportes
        codigos_generales = set(df_generales_cat['codigo'].astype(str).str.strip())
        df_base_generales = df_consolidado[df_consolidado['codigo'].isin(codigos_generales)].copy()
        # Ensure unique codes for general report
        df_base_generales.drop_duplicates(subset=['codigo'], inplace=True)
        
        codigos_especiales = set(df_especiales_cat['codigo'].astype(str).str.strip())
        df_base_especiales = df_consolidado[df_consolidado['codigo'].isin(codigos_especiales)].copy()
        # Ensure unique codes for special report
        df_base_especiales.drop_duplicates(subset=['codigo'], inplace=True)

        # Generar cada reporte llamando a las funciones del módulo generador
        generate_historical_general_stock_report(df_generales_cat, df_base)
        
        generate_stock_report(df_base_generales.copy(), lineas_a_procesar)
        generate_especiales_report(df_consolidado)
        generate_productos_local_json(df_consolidado, lineas_a_procesar)
        generate_stock_generales_json(df_base_generales, df_base_especiales, lineas_a_procesar)
        
        # Copiar reporte_stock_hoy.xlsx al escritorio
        logger.info("Copiando reporte_stock_hoy.xlsx al escritorio...")
        try:
            source_path = os.path.join(settings.SALIDA_DIR, "reporte_stock_hoy.xlsx")
            destination_path = r"C:\Users\ccusi\Desktop\reporte_stock_hoy.xlsx"
            shutil.copy(source_path, destination_path)
            logger.info(f"reporte_stock_hoy.xlsx copiado exitosamente a {destination_path}")
        except Exception as copy_e:
            logger.error(f"Error al copiar reporte_stock_hoy.xlsx al escritorio: {copy_e}")
            logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"Error fatal en el proceso principal: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
