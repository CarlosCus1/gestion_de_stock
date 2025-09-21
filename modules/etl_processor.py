#!/usr/bin/env python3
"""
Procesador ETL - Sistema de Gestión de Stock

Este módulo maneja el procesamiento ETL principal, coordinando
la descarga, transformación y carga de datos de stock.

Integra con el sistema existente (main.py) pero proporciona
una interfaz unificada para el orquestador.
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configuración del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class ETLProcessor:
    """
    Procesador ETL que coordina todas las operaciones de datos.
    """

    def __init__(self):
        self.logger = logging.getLogger("ETLProcessor")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Carga configuración específica para ETL."""
        return {
            "main_script": PROJECT_ROOT / "main.py",
            "timeout": 600,  # 10 minutos
            "working_dir": PROJECT_ROOT
        }

    def run_full_etl(self) -> Dict[str, Any]:
        """
        Ejecuta el proceso ETL completo.

        Returns:
            Dict con resultado de la ejecución
        """
        self.logger.info("🔄 Iniciando proceso ETL completo...")

        result = {
            "process": "etl_full",
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "duration": 0,
            "files_generated": [],
            "error": None
        }

        start_time = datetime.now()

        try:
            # Ejecutar main.py
            cmd = [sys.executable, str(self.config["main_script"])]
            self.logger.info(f"🚀 Ejecutando: {' '.join(cmd)}")

            process = subprocess.run(
                cmd,
                cwd=self.config["working_dir"],
                capture_output=True,
                text=True,
                timeout=self.config["timeout"]
            )

            result["duration"] = (datetime.now() - start_time).total_seconds()

            if process.returncode == 0:
                result["success"] = True
                self.logger.info("✅ ETL completado exitosamente")

                # Intentar identificar archivos generados
                result["files_generated"] = self._identify_generated_files()

            else:
                result["error"] = f"Exit code {process.returncode}"
                self.logger.error(f"❌ ETL falló: {result['error']}")
                if process.stderr:
                    self.logger.error(f"STDERR: {process.stderr}")

        except subprocess.TimeoutExpired:
            result["error"] = f"Timeout después de {self.config['timeout']} segundos"
            self.logger.error(f"⏰ {result['error']}")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"💥 Error inesperado: {e}")

        return result

    def _identify_generated_files(self) -> List[str]:
        """
        Identifica archivos que fueron generados por el ETL.

        Returns:
            Lista de archivos generados
        """
        # Archivos que típicamente genera el ETL
        expected_files = [
            "salida/reporte_stock_hoy.xlsx",
            "salida/productos_local.json",
            "salida/stock_generales.json",
            "salida/reporte_especiales.xlsx",
            "salida/reporte_historico_general_VES.xlsx"
        ]

        generated = []
        for file_path in expected_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                generated.append(file_path)

        return generated

    def validate_etl_output(self) -> Dict[str, Any]:
        """
        Valida que el ETL generó los archivos esperados.

        Returns:
            Dict con resultado de la validación
        """
        self.logger.info("🔍 Validando salida del ETL...")

        validation = {
            "valid": True,
            "files_checked": 0,
            "files_valid": 0,
            "files_missing": [],
            "timestamp": datetime.now().isoformat()
        }

        # Archivos críticos que deben existir
        critical_files = [
            "salida/reporte_stock_hoy.xlsx",
            "salida/productos_local.json"
        ]

        for file_path in critical_files:
            full_path = PROJECT_ROOT / file_path
            validation["files_checked"] += 1

            if full_path.exists() and full_path.stat().st_size > 0:
                validation["files_valid"] += 1
                self.logger.info(f"✅ {file_path}")
            else:
                validation["files_missing"].append(file_path)
                validation["valid"] = False
                self.logger.error(f"❌ {file_path}")

        return validation

    def get_etl_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del proceso ETL.

        Returns:
            Dict con información del estado
        """
        status = {
            "last_run": None,
            "is_running": False,
            "last_success": None,
            "generated_files": [],
            "timestamp": datetime.now().isoformat()
        }

        # TODO: Implementar verificación de estado real
        # Por ahora, verificar archivos recientes

        try:
            # Verificar archivos generados recientemente
            salida_dir = PROJECT_ROOT / "salida"
            if salida_dir.exists():
                for file_path in salida_dir.glob("*"):
                    if file_path.is_file():
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        status["generated_files"].append({
                            "name": file_path.name,
                            "size": file_path.stat().st_size,
                            "modified": mtime.isoformat()
                        })

                        # Actualizar last_run si es más reciente
                        if status["last_run"] is None or mtime > datetime.fromisoformat(status["last_run"]):
                            status["last_run"] = mtime.isoformat()

        except Exception as e:
            self.logger.error(f"Error obteniendo estado ETL: {e}")

        return status


# Instancia global para uso directo
etl_processor = ETLProcessor()

# Funciones de conveniencia para uso directo
def run_full_etl():
    """Función de conveniencia para ejecutar ETL completo."""
    return etl_processor.run_full_etl()

def validate_etl_output():
    """Función de conveniencia para validar salida ETL."""
    return etl_processor.validate_etl_output()

def get_etl_status():
    """Función de conveniencia para obtener estado ETL."""
    return etl_processor.get_etl_status()


if __name__ == "__main__":
    # Ejemplo de uso directo
    import argparse

    parser = argparse.ArgumentParser(description="Procesador ETL - StockDataMatrix")
    parser.add_argument("--run", action="store_true", help="Ejecutar ETL completo")
    parser.add_argument("--validate", action="store_true", help="Validar salida del ETL")
    parser.add_argument("--status", action="store_true", help="Obtener estado del ETL")

    args = parser.parse_args()

    if args.run:
        result = run_full_etl()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.validate:
        result = validate_etl_output()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.status:
        result = get_etl_status()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()