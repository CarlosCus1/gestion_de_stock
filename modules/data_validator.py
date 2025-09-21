#!/usr/bin/env python3
"""
Validador de Datos - Sistema de Gestión de Stock

Este módulo valida la integridad y calidad de los datos generados,
asegurando que los archivos cumplen con los estándares requeridos.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configuración del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class DataValidator:
    """
    Validador de integridad de datos generados.
    """

    def __init__(self):
        self.logger = logging.getLogger("DataValidator")
        self.config = self._load_validation_config()

    def _load_validation_config(self) -> Dict[str, Any]:
        """Carga configuración de validación."""
        return {
            "min_file_size": 100,  # Bytes mínimos
            "required_files": [
                "salida/reporte_stock_hoy.xlsx",
                "salida/productos_local.json"
            ],
            "json_schema_check": False,  # Por ahora desactivado
            "excel_structure_check": True
        }

    def validate_files(self, files: List[str], base_dir: str = None) -> Dict[str, Any]:
        """
        Valida una lista de archivos.

        Args:
            files: Lista de archivos a validar
            base_dir: Directorio base (opcional)

        Returns:
            Dict con resultados de validación
        """
        if base_dir is None:
            base_dir = PROJECT_ROOT

        self.logger.info(f"🔍 Validando {len(files)} archivos...")

        validation_results = {
            "total_files": len(files),
            "valid_files": 0,
            "invalid_files": 0,
            "file_results": [],
            "timestamp": datetime.now().isoformat(),
            "overall_valid": True
        }

        for file_path in files:
            result = self.validate_single_file(file_path, base_dir)
            validation_results["file_results"].append(result)

            if result["valid"]:
                validation_results["valid_files"] += 1
            else:
                validation_results["invalid_files"] += 1
                validation_results["overall_valid"] = False

        self.logger.info(f"📊 Validación completada: {validation_results['valid_files']}/{validation_results['total_files']} archivos válidos")

        return validation_results

    def validate_single_file(self, file_path: str, base_dir: Path) -> Dict[str, Any]:
        """
        Valida un archivo individual.

        Args:
            file_path: Ruta del archivo a validar
            base_dir: Directorio base

        Returns:
            Dict con resultado de validación
        """
        full_path = base_dir / file_path

        result = {
            "file": file_path,
            "exists": False,
            "size": 0,
            "readable": False,
            "valid": False,
            "errors": [],
            "warnings": []
        }

        # Verificar existencia
        if not full_path.exists():
            result["errors"].append("Archivo no existe")
            return result

        result["exists"] = True

        try:
            stat = full_path.stat()
            result["size"] = stat.st_size

            # Verificar tamaño mínimo
            if result["size"] < self.config["min_file_size"]:
                result["warnings"].append(f"Archivo muy pequeño ({result['size']} bytes)")

            # Verificar si es legible
            if full_path.suffix.lower() in ['.json', '.txt', '.csv']:
                result["readable"] = self._validate_text_file(full_path)
            elif full_path.suffix.lower() in ['.xlsx', '.xls']:
                result["readable"] = self._validate_excel_file(full_path)
            else:
                result["readable"] = True  # Asumir válido para otros tipos

            # Determinar validez general
            result["valid"] = result["exists"] and result["readable"] and len(result["errors"]) == 0

        except Exception as e:
            result["errors"].append(f"Error accediendo al archivo: {str(e)}")

        return result

    def _validate_text_file(self, file_path: Path) -> bool:
        """
        Valida archivo de texto (JSON, CSV, etc.).

        Args:
            file_path: Ruta del archivo

        Returns:
            True si es válido
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1024)  # Leer primeros 1KB

                # Validación específica por tipo
                if file_path.suffix.lower() == '.json':
                    try:
                        json.loads(content)
                        return True
                    except json.JSONDecodeError:
                        return False

                return len(content.strip()) > 0

        except Exception:
            return False

    def _validate_excel_file(self, file_path: Path) -> bool:
        """
        Valida archivo Excel.

        Args:
            file_path: Ruta del archivo

        Returns:
            True si es válido
        """
        try:
            import pandas as pd

            # Intentar leer el archivo
            df = pd.read_excel(file_path, nrows=5)  # Leer solo primeras 5 filas

            # Verificar que tenga datos
            return len(df) > 0 and len(df.columns) > 0

        except Exception:
            return False

    def validate_critical_files(self) -> Dict[str, Any]:
        """
        Valida archivos críticos del sistema.

        Returns:
            Dict con resultados de validación
        """
        self.logger.info("🔍 Validando archivos críticos...")

        return self.validate_files(self.config["required_files"])

    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """
        Genera un reporte legible de los resultados de validación.

        Args:
            validation_results: Resultados de validación

        Returns:
            String con el reporte formateado
        """
        report_lines = [
            "📋 REPORTE DE VALIDACIÓN DE DATOS",
            "=" * 50,
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Archivos totales: {validation_results['total_files']}",
            f"Archivos válidos: {validation_results['valid_files']}",
            f"Archivos inválidos: {validation_results['invalid_files']}",
            "",
            "DETALLE POR ARCHIVO:",
            "-" * 30
        ]

        for file_result in validation_results["file_results"]:
            status = "✅" if file_result["valid"] else "❌"
            report_lines.append(f"{status} {file_result['file']}")

            if file_result["size"] > 0:
                report_lines.append(f"   Tamaño: {file_result['size']:,} bytes")

            if file_result["errors"]:
                report_lines.extend([f"   ❌ {error}" for error in file_result["errors"]])

            if file_result["warnings"]:
                report_lines.extend([f"   ⚠️ {warning}" for warning in file_result["warnings"]])

            report_lines.append("")

        report_lines.extend([
            "=" * 50,
            f"Estado general: {'✅ VÁLIDO' if validation_results['overall_valid'] else '❌ INVÁLIDO'}"
        ])

        return "\n".join(report_lines)


# Instancia global para uso directo
data_validator = DataValidator()

# Funciones de conveniencia para uso directo
def validate_files(files, base_dir=None):
    """Función de conveniencia para validar archivos."""
    return data_validator.validate_files(files, base_dir)

def validate_single_file(file_path, base_dir=None):
    """Función de conveniencia para validar un archivo."""
    if base_dir is None:
        base_dir = PROJECT_ROOT
    return data_validator.validate_single_file(file_path, base_dir)

def validate_critical_files():
    """Función de conveniencia para validar archivos críticos."""
    return data_validator.validate_critical_files()

def generate_validation_report(validation_results):
    """Función de conveniencia para generar reporte de validación."""
    return data_validator.generate_validation_report(validation_results)


if __name__ == "__main__":
    # Ejemplo de uso directo
    import argparse

    parser = argparse.ArgumentParser(description="Validador de Datos - StockDataMatrix")
    parser.add_argument("--files", nargs="+", help="Archivos a validar")
    parser.add_argument("--critical", action="store_true", help="Validar archivos críticos")
    parser.add_argument("--report", action="store_true", help="Generar reporte detallado")

    args = parser.parse_args()

    if args.critical:
        result = validate_critical_files()

    elif args.files:
        result = validate_files(args.files)

    else:
        print("❌ Especifique --files o --critical")
        sys.exit(1)

    # Mostrar resultados
    if args.report:
        print(generate_validation_report(result))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))