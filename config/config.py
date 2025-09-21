
import os

class Settings:
    # Project root
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Input directories and files
    DATA_SOURCES_DIR = os.path.join(BASE_DIR, "data_sources")
    INPUT_STOCK_MODELO_COLOR = os.path.join(DATA_SOURCES_DIR, "raw_reports", "STOCK_MODELO_COLOR.xls")
    INPUT_ESPECIALES_EXCEL = os.path.join(DATA_SOURCES_DIR, "catalogs", "codigos_especiales.xlsx") # Assuming this file exists

    # Output directories - TODO EN UNA SOLA CARPETA
    OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
    REPORTS_DIR = os.path.join(OUTPUTS_DIR, "reports")
    # JSON_EXPORTS_DIR = os.path.join(OUTPUTS_DIR, "json_exports")  # DEPRECATED - Usar REPORTS_DIR para todo

    # Temp directory
    TEMP_DIR = os.path.join(BASE_DIR, ".temp", "processing")
    HISTORICOS_DIR = os.path.join(TEMP_DIR, "historicos")


    # Output files - TODOS EN REPORTS_DIR
    OUTPUT_FINAL_REPORT_EXCEL = os.path.join(REPORTS_DIR, "reporte_stock_hoy.xlsx")
    OUTPUT_ESPECIALES_REPORT_EXCEL = os.path.join(REPORTS_DIR, "reporte_especiales.xlsx")
    OUTPUT_PRODUCTOS_LOCAL_JSON = os.path.join(REPORTS_DIR, "productos_local.json")
    STOCK_GENERALES_FILE = os.path.join(REPORTS_DIR, "stock_generales.json")
    
    # Table styles for Excel reports
    TABLE_STYLES = [
        'Table Style Medium 9',
        'Table Style Medium 10',
        'Table Style Medium 11',
        'Table Style Medium 12',
        'Table Style Medium 13',
        'Table Style Medium 14',
        'Table Style Medium 15',
        'Table Style Medium 16',
    ]

settings = Settings()
