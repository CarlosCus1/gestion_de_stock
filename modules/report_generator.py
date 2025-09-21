#!/usr/bin/env python3
"""
Generador Unificado de Reportes - Sistema de Gestión de Stock

Este módulo centraliza todas las funciones de generación de reportes,
proporcionando una interfaz unificada para crear diferentes tipos de reportes.

Funciones disponibles:
- generate_stock_report(): Reporte general de stock
- generate_color_report(): Reporte de colores por código
- generate_holiday_report(): Reporte de feriados
- generate_special_report(): Reporte de códigos especiales
- generate_historical_report(): Reporte histórico VES
"""

import os
import sys
import json
import pandas as pd
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configuración del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# No importar configuración antigua para evitar conflictos

class ReportGenerator:
    """
    Generador unificado de reportes para el sistema StockDataMatrix.
    """

    def __init__(self):
        self.logger = logging.getLogger("ReportGenerator")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Carga configuración específica para reportes."""
        return {
            "reports_dir": str(PROJECT_ROOT / "outputs" / "reports"),
            "data_sources_dir": str(PROJECT_ROOT / "data_sources"),
            "table_styles": [
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
        }

    def generate_stock_report(self, data: pd.DataFrame = None) -> List[str]:
        """
        Genera reporte general de stock.

        Args:
            data: DataFrame con datos de stock (opcional)

        Returns:
            Lista de archivos generados
        """
        self.logger.info("📊 Generando reporte general de stock...")

        # TODO: Implementar lógica real usando main.py existente
        # Por ahora, placeholder que indica que se debe usar el ETL principal

        self.logger.info("ℹ️ Reporte general debe generarse via ETL principal (main.py)")
        return ["reporte_stock_hoy.xlsx", "productos_local.json", "stock_generales.json"]

    def generate_color_report(self) -> List[str]:
        """
        Genera reporte de colores por código.

        Returns:
            Lista de archivos generados
        """
        self.logger.info("🎨 Generando reporte de colores...")

        try:
            # Importar y ejecutar el generador existente
            from scripts.generate_colores_json import generate_colores_files

            success = generate_colores_files()
            if success:
                return ["stock_color.xlsx", "colores_por_codigo.json"]
            else:
                self.logger.error("❌ Falló generación de colores")
                return []

        except Exception as e:
            self.logger.error(f"❌ Error en generación de colores: {e}")
            return []

    def generate_holiday_report(self) -> List[str]:
        """
        Genera reporte de feriados.

        Returns:
            Lista de archivos generados
        """
        self.logger.info("📅 Generando reporte de feriados...")

        try:
            # Importar y ejecutar el generador existente
            from scripts.generate_feriados_json import generate_feriados_json

            success = generate_feriados_json()
            if success:
                return ["feriados.json"]
            else:
                self.logger.error("❌ Falló generación de feriados")
                return []

        except Exception as e:
            self.logger.error(f"❌ Error en generación de feriados: {e}")
            return []

    def generate_special_report(self, data: pd.DataFrame = None) -> List[str]:
        """
        Genera reporte de códigos especiales.

        Args:
            data: DataFrame con datos de stock (opcional)

        Returns:
            Lista de archivos generados
        """
        self.logger.info("⭐ Generando reporte de códigos especiales...")

        # TODO: Implementar lógica real
        # Por ahora, placeholder

        self.logger.info("ℹ️ Reporte especial debe generarse via ETL principal")
        return ["reporte_especiales.xlsx"]

    def generate_historical_report(self, data: pd.DataFrame = None) -> List[str]:
        """
        Genera reporte histórico VES.

        Args:
            data: DataFrame con datos de stock (opcional)

        Returns:
            Lista de archivos generados
        """
        self.logger.info("📈 Generando reporte histórico VES...")

        # TODO: Implementar lógica real
        # Por ahora, placeholder

        self.logger.info("ℹ️ Reporte histórico debe generarse via ETL principal")
        return ["reporte_historico_general_VES.xlsx"]

    def generate_report_by_type(self, report_type: str, **kwargs) -> List[str]:
        """
        Genera un reporte específico por tipo.

        Args:
            report_type: Tipo de reporte ('stock', 'colors', 'holidays', 'special', 'historical')
            **kwargs: Argumentos adicionales para el reporte

        Returns:
            Lista de archivos generados
        """
        report_map = {
            'stock': self.generate_stock_report,
            'colors': self.generate_color_report,
            'holidays': self.generate_holiday_report,
            'special': self.generate_special_report,
            'historical': self.generate_historical_report
        }

        if report_type not in report_map:
            self.logger.error(f"❌ Tipo de reporte desconocido: {report_type}")
            return []

        return report_map[report_type](**kwargs)

    def validate_generated_files(self, files: List[str]) -> Dict[str, bool]:
        """
        Valida que los archivos generados existen y no están vacíos.

        Args:
            files: Lista de archivos a validar

        Returns:
            Dict con estado de validación por archivo
        """
        validation_results = {}

        for file_path in files:
            full_path = os.path.join(self.config["reports_dir"], file_path)

            exists = os.path.exists(full_path)
            not_empty = exists and os.path.getsize(full_path) > 0

            validation_results[file_path] = {
                "exists": exists,
                "not_empty": not_empty,
                "valid": exists and not_empty
            }

            if not exists:
                self.logger.warning(f"⚠️ Archivo no encontrado: {file_path}")
            elif not not_empty:
                self.logger.warning(f"⚠️ Archivo vacío: {file_path}")
            else:
                self.logger.info(f"✅ Archivo válido: {file_path}")

        return validation_results

    def get_report_info(self, report_type: str = None) -> Dict[str, Any]:
        """
        Obtiene información sobre reportes disponibles.

        Args:
            report_type: Tipo específico de reporte (opcional)

        Returns:
            Información sobre reportes
        """
        all_reports = {
            'stock': {
                'name': 'Stock General',
                'description': 'Reportes principales de stock diario',
                'files': ['reporte_stock_hoy.xlsx', 'productos_local.json', 'stock_generales.json'],
                'frequency': 'daily'
            },
            'colors': {
                'name': 'Colores por Código',
                'description': 'Análisis detallado de stock por colores',
                'files': ['stock_color.xlsx', 'colores_por_codigo.json'],
                'frequency': 'daily'
            },
            'holidays': {
                'name': 'Feriados',
                'description': 'Calendario de feriados peruanos',
                'files': ['feriados.json'],
                'frequency': 'on_change'
            },
            'special': {
                'name': 'Códigos Especiales',
                'description': 'Análisis de códigos especiales',
                'files': ['reporte_especiales.xlsx'],
                'frequency': 'daily'
            },
            'historical': {
                'name': 'Histórico VES',
                'description': 'Análisis histórico con tendencias VES',
                'files': ['reporte_historico_general_VES.xlsx'],
                'frequency': 'daily'
            }
        }

        if report_type:
            return all_reports.get(report_type, {})

        return all_reports


# Instancia global para uso directo
report_generator = ReportGenerator()

# Funciones de conveniencia para uso directo
def generate_stock_report(data=None):
    """Función de conveniencia para generar reporte de stock."""
    return report_generator.generate_stock_report(data)

def generate_color_report():
    """Función de conveniencia para generar reporte de colores."""
    return report_generator.generate_color_report()

def generate_holiday_report():
    """Función de conveniencia para generar reporte de feriados."""
    return report_generator.generate_holiday_report()

def generate_special_report(data=None):
    """Función de conveniencia para generar reporte especial."""
    return report_generator.generate_special_report(data)

def generate_historical_report(data=None):
    """Función de conveniencia para generar reporte histórico."""
    return report_generator.generate_historical_report()

def generate_report_by_type(report_type, **kwargs):
    """Función de conveniencia para generar reporte por tipo."""
    return report_generator.generate_report_by_type(report_type, **kwargs)

def validate_generated_files(files):
    """Función de conveniencia para validar archivos."""
    return report_generator.validate_generated_files(files)

def get_report_info(report_type=None):
    """Función de conveniencia para obtener información de reportes."""
    return report_generator.get_report_info(report_type)


if __name__ == "__main__":
    # Ejemplo de uso directo
    import argparse

    parser = argparse.ArgumentParser(description="Generador de Reportes - StockDataMatrix")
    parser.add_argument("--type", required=True, help="Tipo de reporte (stock, colors, holidays, special, historical)")
    parser.add_argument("--validate", action="store_true", help="Validar archivos generados")

    args = parser.parse_args()

    # Generar reporte
    files = generate_report_by_type(args.type)

    if files:
        print(f"✅ Reporte {args.type} generado: {files}")

        if args.validate:
            validation = validate_generated_files(files)
            print("📋 Validación:")
            for file, status in validation.items():
                status_icon = "✅" if status["valid"] else "❌"
                print(f"  {status_icon} {file}: {status}")
    else:
        print(f"❌ Error generando reporte {args.type}")
        sys.exit(1)