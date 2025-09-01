import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Settings:
    """
    Clase para centralizar toda la configuración del proyecto.
    Las configuraciones sensibles o específicas del entorno se cargan desde variables de entorno.
    """
    # === DIRECTORIOS ===
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATOS_DIR = os.path.join(BASE_DIR, "datos")
    SALIDA_DIR = os.path.join(BASE_DIR, "salida")
    PROCESAMIENTO_DIR = os.path.join(BASE_DIR, "procesamiento")
    LOGS_DIR = os.path.join(PROCESAMIENTO_DIR, "logs")
    HISTORICOS_DIR = os.path.join(PROCESAMIENTO_DIR, "historicos")
    TEMP_DIR = os.path.join(PROCESAMIENTO_DIR, "temp")
    
    REQUIRED_DIRS = [DATOS_DIR, SALIDA_DIR, PROCESAMIENTO_DIR, LOGS_DIR, HISTORICOS_DIR, TEMP_DIR]

    # === ARCHIVOS DE ENTRADA ===
    INPUT_GENERALES_EXCEL = os.path.join(DATOS_DIR, "codigos_generales.xlsx")
    INPUT_ESPECIALES_EXCEL = os.path.join(DATOS_DIR, "codigos_especiales.xlsx")
    INPUT_LINES_TO_PROCESS_EXCEL = os.path.join(DATOS_DIR, "lineas_a_procesar.xlsx")
    INPUT_BASE_TOTAL = os.path.join(DATOS_DIR, "base_total.xls")

    # === ARCHIVOS DE SALIDA (Resultados Finales) ===
    OUTPUT_FINAL_REPORT_EXCEL = os.path.join(SALIDA_DIR, "reporte_stock_hoy.xlsx")
    OUTPUT_ESPECIALES_REPORT_EXCEL = os.path.join(SALIDA_DIR, "reporte_especiales.xlsx")
    OUTPUT_PRODUCTOS_LOCAL_JSON = os.path.join(SALIDA_DIR, "productos_local.json")
    STOCK_GENERALES_FILE = os.path.join(SALIDA_DIR, "stock_generales.json")
    REPORTES_DIR = SALIDA_DIR
    
    # === ARCHIVOS DE PROCESAMIENTO (Archivos de Trabajo) ===
    DATA_STOCK_COMPLETO_FILE = os.path.join(PROCESAMIENTO_DIR, "data_stock_completo.xlsx")
    PREVIOUS_STOCK_FILE = os.path.join(TEMP_DIR, "previous_stock.json")

    # === API & DESCARGAS (desde .env) ===
    STOCK_API_URL = os.getenv("STOCK_API_URL", "http://default.url/if/not/set")

    # === GOOGLE CLOUD STORAGE (desde .env) ===
    STORAGE_BUCKET_NAME = os.getenv("STORAGE_BUCKET_NAME")
    STORAGE_CREDENTIALS_PATH = os.getenv("STORAGE_CREDENTIALS_PATH")

    # === REPORTES & PROCESAMIENTO ===
    PALETA_LINEAS = {
        'PELOTAS': '#1F77B4', 'PINTURA': '#2CA02C', 'ESCRITURA': '#D62728',
        'MANUALIDADES': '#9467BD', 'DIBUJO': '#8C564B', 'MASCOTAS': '#E377C2',
        'JUGUETES': '#7F7F7F', 'ACCESORIOS': '#BCBD22', 'FORROS': '#17BECF',
        'PEGAMENTOS': '#FF7F0E', 'PUBLICIDAD': '#7E7E7E', 'METALICA': '#555555',
        'PRODUCTOS INDUSTRIALES': '#33A1C9', 'OTROS': '#999999',
        'REPRESENTADAS': '#A6761D', 'ARCHIVO': '#8B4513',
        'ACCESORIOS DEPORTIVOS': '#00FF00'
    }

    TABLE_STYLES = [
        'Table Style Medium 1', 'Table Style Medium 2', 'Table Style Medium 3',
        'Table Style Medium 4', 'Table Style Medium 5', 'Table Style Medium 6',
        'Table Style Medium 7', 'Table Style Medium 8', 'Table Style Medium 9',
        'Table Style Medium 10', 'Table Style Medium 11', 'Table Style Medium 12',
        'Table Style Medium 13', 'Table Style Medium 14', 'Table Style Medium 15',
        'Table Style Medium 16', 'Table Style Medium 17', 'Table Style Medium 18',
        'Table Style Medium 19', 'Table Style Medium 20', 'Table Style Medium 21',
        'Table Style Medium 22', 'Table Style Medium 23', 'Table Style Medium 24',
        'Table Style Medium 25', 'Table Style Medium 26', 'Table Style Medium 27',
        'Table Style Medium 28'
    ]

    # === CONFIGURACIÓN DE HISTÓRICOS ===
    HISTORICO_STOCK_COLUMN = 'VES_disponible'

    # === ESTANDARIZACIÓN DE COLUMNAS ===
    STANDARD_COLUMN_NAMES = {
        'codigo': 'codigo',
        'nombre': 'nombre',
        'linea': 'linea',
        'orden': 'orden',
        'u_por_caja': 'u_por_caja',
        'ean': 'ean',
        'ean_14': 'ean_14',
        'stock_referencial': 'stock_referencial',
        'precio': 'precio',
        'can_kg_um': 'can_kg_um'
    }

    BASE_TOTAL_COLS_MAP = {
        'CODIGO': STANDARD_COLUMN_NAMES['codigo'],
        'NOMBRE': STANDARD_COLUMN_NAMES['nombre'],
        'LINEA': STANDARD_COLUMN_NAMES['linea'],
        'COD_EAN': STANDARD_COLUMN_NAMES['ean'],
        'COD_EAN_14': STANDARD_COLUMN_NAMES['ean_14'],
        'PRECIO': STANDARD_COLUMN_NAMES['precio'],
        'CAN_KG_UM': STANDARD_COLUMN_NAMES['can_kg_um']
    }

    REPT_STOCK_COLS_MAP = {
        'ARTÍCULO': STANDARD_COLUMN_NAMES['codigo'],
        'NOMBRE_ARTICULO': 'nombre_articulo',
        'ALMACEN': 'almacen',
        'STOCK TOTAL': 'stock_total',
        'PREDESPACHO': 'predespacho',
        'DISPONIBLE': 'disponible'
    }
    
    MANUAL_COLS_MAP = {
        'CODIGO': STANDARD_COLUMN_NAMES['codigo'],
        'NOMBRE': STANDARD_COLUMN_NAMES['nombre'],
        'LINEA': STANDARD_COLUMN_NAMES['linea'],
        'ORDEN': STANDARD_COLUMN_NAMES['orden'],
        'UNID_MASTER': STANDARD_COLUMN_NAMES['u_por_caja'],
        'MOTIVO': 'motivo'
    }

settings = Settings()