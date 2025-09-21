"""
Módulos especializados del Sistema de Gestión de Stock

Este paquete contiene todos los módulos especializados que son
coordinados por el orquestador principal.
"""

__version__ = "2.0.0"
__author__ = "StockDataMatrix Team"

# Lista de módulos disponibles
AVAILABLE_MODULES = [
    "etl_processor",
    "report_generator",
    "file_delivery",
    "data_validator",
    "scheduler"
]

def get_module_info():
    """Retorna información sobre los módulos disponibles."""
    return {
        "version": __version__,
        "modules": AVAILABLE_MODULES,
        "description": "Módulos especializados para el sistema de gestión de stock"
    }