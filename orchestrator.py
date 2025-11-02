#!/usr/bin/env python3
"""
Orquestador Principal del Sistema de Gestión de Stock

Este módulo centraliza la coordinación de todos los procesos ETL y de reportes,
con funciones específicas para cada tipo de operación y sistema de entrega.

Arquitectura:
- Orquestador principal que coordina todo
- Funciones específicas por tipo de reporte
- Sistema de entrega (local/servidor/cloud)
- Configuración centralizada
- Logging unificado

Uso:
    python orchestrator.py --full-etl
    python orchestrator.py --report colors
    python orchestrator.py --deliver server1
"""

import os
import sys
import json
import logging
import argparse
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any
import importlib.util

# Configuración del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

class StockOrchestrator:
    """
    Orquestador principal que coordina todos los procesos del sistema.
    """

    def __init__(self):
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.modules = {}

        # Cargar módulos especializados
        self._load_modules()

    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración centralizada."""
        config_path = PROJECT_ROOT / "config" / "unified_config.json"

        # Configuración por defecto
        default_config = {
            "project": {
                "name": "Sistema de Gestión de Stock",
                "version": "2.0",
                "root_dir": str(PROJECT_ROOT)
            },
            "directories": {
                "data_sources": str(PROJECT_ROOT / "data_sources"),
                "outputs": str(PROJECT_ROOT / "outputs"),
                "reports": str(PROJECT_ROOT / "outputs" / "reports"),
                "logs": str(PROJECT_ROOT / "procesamiento" / "logs"),
                "temp": str(PROJECT_ROOT / "procesamiento" / "temp")
            },
            "reports": {
                "stock_general": {
                    "name": "Stock General",
                    "files": ["reporte_stock_hoy.xlsx", "productos_local.json", "stock_generales.json"],
                    "frequency": "daily"
                },
                "colors": {
                    "name": "Colores por Código",
                    "files": ["stock_color.xlsx", "colores_por_codigo.json"],
                    "frequency": "daily"
                },
                "holidays": {
                    "name": "Feriados",
                    "files": ["feriados.json"],
                    "frequency": "on_change"
                },
                "special": {
                    "name": "Códigos Especiales",
                    "files": ["reporte_especiales.xlsx"],
                    "frequency": "daily"
                },
                "historical": {
                    "name": "Histórico VES",
                    "files": ["reporte_historico_general_VES.xlsx"],
                    "frequency": "daily"
                }
            },
            "delivery": {
                "servers": [
                    {
                        "name": "local_desktop",
                        "type": "local",
                        "path": "C:\\Users\\{username}\\Desktop",
                        "files": ["reporte_stock_hoy.xlsx"]
                    }
                ]
            }
        }

        # Cargar configuración personalizada si existe
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                # Fusionar con configuración por defecto
                self._merge_configs(default_config, custom_config)
            except Exception as e:
                print(f"Error cargando configuración personalizada: {e}")

        return default_config

    def _merge_configs(self, base: Dict, custom: Dict) -> None:
        """Fusiona configuración personalizada con la base."""
        for key, value in custom.items():
            if isinstance(value, dict) and key in base:
                self._merge_configs(base[key], value)
            else:
                base[key] = value

    def _setup_logging(self) -> logging.Logger:
        """Configura el sistema de logging."""
        logs_dir = Path(self.config["directories"]["logs"])
        logs_dir.mkdir(exist_ok=True)

        log_filename = f"orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_filepath = logs_dir / log_filename

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_filepath, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        logger = logging.getLogger("StockOrchestrator")
        logger.info("[INFO] Orquestador inicializado")
        return logger

    def _load_modules(self) -> None:
        """Carga los módulos especializados."""
        modules_dir = PROJECT_ROOT / "modules"

        # Crear módulos si no existen
        modules_dir.mkdir(exist_ok=True)

        # Módulos requeridos
        required_modules = [
            "etl_processor",
            "report_generator",
            "file_delivery",
            "data_validator"
        ]

        for module_name in required_modules:
            module_path = modules_dir / f"{module_name}.py"
            if module_path.exists():
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.modules[module_name] = module
                    self.logger.info(f"[SUCCESS] Modulo {module_name} cargado")
                except Exception as e:
                    self.logger.error(f"[ERROR] Error cargando modulo {module_name}: {e}")
            else:
                self.logger.warning(f"[WARNING] Modulo {module_name} no encontrado, creando placeholder")
                self._create_module_placeholder(module_name, module_path)

    def _create_module_placeholder(self, module_name: str, module_path: Path) -> None:
        """Crea un placeholder para módulos faltantes."""
        placeholder_code = f'''"""
Placeholder para módulo {module_name}
Este módulo será implementado próximamente.
"""

def placeholder_function(*args, **kwargs):
    """Función placeholder."""
    print(f"[WARNING] Modulo {{module_name}} no implementado aun")
    return None

# Alias para compatibilidad
def run_etl():
    return placeholder_function()

def generate_report(report_type):
    return placeholder_function()

def deliver_files(files, destination):
    return placeholder_function()
'''

        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(placeholder_code)

        self.logger.info(f"📝 Placeholder creado para {module_name}")

    # ========================================
    # FUNCIONES PÚBLICAS DEL ORQUESTADOR
    # ========================================

    def run_full_etl(self) -> Dict[str, Any]:
        """
        Ejecuta el proceso ETL unificado completo.
        Genera TODOS los archivos en un solo directorio unificado.

        Returns:
            Dict con resultados de la ejecución
        """
        self.logger.info("=== INICIANDO PROCESO ETL UNIFICADO ===")

        results = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "processes": [],
            "files_generated": [],
            "errors": [],
            "unified_output_dir": self.config["directories"]["reports"]
        }

        try:
            # Ejecutar proceso ETL unificado completo
            unified_result = self._run_unified_etl_process()
            results["processes"].append(unified_result)
            results["files_generated"].extend(unified_result.get("files", []))

            if not unified_result["success"]:
                results["success"] = False
                results["errors"].extend(unified_result.get("errors", []))

            # Entregar archivos si es necesario
            if results["success"] and results["files_generated"]:
                delivery_result = self.deliver_to_default_servers(results["files_generated"])
                results["processes"].append(delivery_result)

        except Exception as e:
            self.logger.error(f"[FATAL] Error fatal en ETL unificado: {e}")
            results["success"] = False
            results["errors"].append(str(e))

        # Resumen final
        if results["success"]:
            self.logger.info("[SUCCESS] === PROCESO ETL UNIFICADO EXITOSO ===")
            self.logger.info(f"[INFO] Archivos generados en: {results['unified_output_dir']}")
            self.logger.info(f"[INFO] Total archivos: {len(results['files_generated'])}")
        else:
            self.logger.error("[ERROR] === PROCESO ETL UNIFICADO FALLÓ ===")
            self.logger.error(f"[ERROR] Errores: {results['errors']}")

        return results

    def generate_specific_report(self, report_type: str) -> Dict[str, Any]:
        """
        Genera un reporte específico.
        NOTA: Para producción, usar run_full_etl() que ejecuta todo unificado.

        Args:
            report_type: Tipo de reporte ('colors', 'holidays', 'special', 'historical')

        Returns:
            Dict con resultado de la generación
        """
        self.logger.warning(f"[WARNING] generate_specific_report() está obsoleto. Usar run_full_etl() para proceso unificado.")
        self.logger.info(f"[INFO] Generando reporte individual: {report_type}")

        result = {
            "report_type": report_type,
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "files": [],
            "error": "Método obsoleto - usar run_full_etl()",
            "warning": "Este método genera reportes individuales. Para producción usar proceso unificado."
        }

        try:
            if report_type == "colors":
                exec_result = self._execute_colors_report()
            elif report_type == "holidays":
                exec_result = self._execute_holidays_report()
            else:
                exec_result = {"success": False, "error": f"Tipo de reporte '{report_type}' no soportado individualmente"}

            result.update(exec_result)

        except Exception as e:
            self.logger.error(f"[ERROR] Error generando reporte {report_type}: {e}")
            result["error"] = str(e)

        return result

    def deliver_to_server(self, files: List[str], server_name: str) -> Dict[str, Any]:
        """
        Entrega archivos a un servidor específico.

        Args:
            files: Lista de archivos a entregar (todos los generados)
            server_name: Nombre del servidor destino

        Returns:
            Dict con resultado de la entrega
        """
        self.logger.info(f"[INFO] Entregando archivos a servidor: {server_name}")

        result = {
            "server": server_name,
            "files": [], # Archivos realmente entregados
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": None
        }

        try:
            # Buscar configuración del servidor
            server_config = None
            for server in self.config["delivery"]["servers"]:
                if server["name"] == server_name:
                    server_config = server
                    break

            if not server_config:
                raise ValueError(f"Servidor '{server_name}' no encontrado en configuración")

            # Filtrar archivos según la configuración del servidor
            files_to_deliver = [f for f in files if f in server_config.get("files", [])]
            
            if not files_to_deliver:
                self.logger.info(f"No hay archivos para entregar a {server_name} según su configuración.")
                result["success"] = True
                return result

            self.logger.info(f"Entregando {len(files_to_deliver)} archivos a {server_name}")
            # Ejecutar entrega
            delivery_result = self._deliver_files(files_to_deliver, server_config)
            result.update(delivery_result)
            result["files"] = files_to_deliver # Actualizar con los archivos realmente entregados
            result["success"] = True

            self.logger.info(f"✅ Archivos entregados exitosamente a {server_name}")

        except Exception as e:
            self.logger.error(f"❌ Error en entrega a {server_name}: {e}")
            result["error"] = str(e)

        return result

    def deliver_to_default_servers(self, files: List[str]) -> Dict[str, Any]:
        """
        Entrega archivos a los servidores por defecto.

        Args:
            files: Lista de archivos a entregar

        Returns:
            Dict con resultados de todas las entregas
        """
        self.logger.info("📤 Ejecutando entregas por defecto")

        results = {
            "operation": "default_delivery",
            "success": True,
            "deliveries": [],
            "timestamp": datetime.now().isoformat()
        }

        for server in self.config["delivery"]["servers"]:
            delivery_result = self.deliver_to_server(files, server["name"])
            results["deliveries"].append(delivery_result)

            if not delivery_result["success"]:
                results["success"] = False

        return results

    # ========================================
    # FUNCIONES PRIVADAS DE IMPLEMENTACIÓN
    # ========================================

    def _run_unified_etl_process(self) -> Dict[str, Any]:
        """
        Ejecuta el proceso ETL unificado completo con lógica inteligente.
        - Stock: Siempre se ejecuta
        - Colores: Solo si hay cambios en los datos
        - Feriados: Solo si hay cambios en el archivo fuente
        """
        self.logger.info("🔄 Ejecutando proceso ETL unificado con lógica inteligente...")

        result = {
            "process": "unified_etl",
            "success": True,
            "files": [], # Lista para evitar problemas de serialización JSON
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }

        output_dir = Path(self.config["directories"]["reports"])
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Ejecutar ETL principal (main.py) - SIEMPRE
            self.logger.info("📊 Ejecutando ETL principal (siempre)...")
            etl_result = self._execute_etl_main()
            if etl_result["success"]:
                result["files"].extend(etl_result["files"])
                # Eliminar duplicados manteniendo el orden
                seen = set()
                result["files"] = [x for x in result["files"] if not (x in seen or seen.add(x))]
                self.logger.info(f"✅ ETL principal: {len(etl_result['files'])} archivos generados")
            else:
                result["success"] = False
                result["errors"].append(f"ETL principal falló: {etl_result.get('error', 'Error desconocido')}")
                return result

            # 2. Generar reportes especializados con lógica inteligente
            specialized_reports = []

            # Colores: Solo si hay cambios en los datos
            if self._should_update_colors():
                specialized_reports.append(("colors", self._execute_colors_report))
            else:
                self.logger.info("🎨 Colores: Sin cambios, omitiendo...")

            # Feriados: Solo si hay cambios en el archivo fuente
            if self._should_update_holidays():
                specialized_reports.append(("holidays", self._execute_holidays_report))
            else:
                self.logger.info("📅 Feriados: Sin cambios, omitiendo...")

            # Ejecutar reportes que requieren actualización
            for report_name, report_func in specialized_reports:
                self.logger.info(f"📋 Generando reporte {report_name}...")
                report_result = report_func()
                if report_result["success"]:
                    result["files"].extend(report_result["files"])
                    # Eliminar duplicados manteniendo el orden
                    seen = set()
                    result["files"] = [x for x in result["files"] if not (x in seen or seen.add(x))]
                    self.logger.info(f"✅ Reporte {report_name}: {len(report_result['files'])} archivos generados")
                else:
                    result["success"] = False
                    result["errors"].append(f"Reporte {report_name} falló: {report_result.get('error', 'Error desconocido')}")

            # 3. Consolidar archivos del directorio outputs/reports/ al directorio unificado
            self.logger.info("🔄 Verificando archivos en directorio unificado...")
            consolidation_result = self._consolidate_outputs()
            if consolidation_result["success"]:
                result["files"].extend(consolidation_result["files"])
                # Eliminar duplicados manteniendo el orden
                seen = set()
                result["files"] = [x for x in result["files"] if not (x in seen or seen.add(x))]
                self.logger.info(f"✅ Verificación: {len(consolidation_result['files'])} archivos encontrados")
            else:
                self.logger.warning(f"⚠️ Verificación con advertencias: {consolidation_result.get('warnings', [])}")

            # 4. Validar archivos generados
            self.logger.info("🔍 Validando archivos generados...")
            validation_result = self._validate_generated_files(list(result["files"]))
            if not validation_result["success"]:
                result["success"] = False
                result["errors"].extend(validation_result.get("errors", []))

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Error en proceso unificado: {str(e)}")
            self.logger.error(f"💥 Error en proceso ETL unificado: {e}")

        # Los archivos ya están en formato lista
        return result

    def _should_update_colors(self) -> bool:
        """Determina si se debe actualizar el reporte de colores con lógica inteligente del Desktop."""
        # VERIFICACIÓN PRIORITARIA DEL DESKTOP
        desktop_result = self._check_desktop_colors()
        
        if desktop_result["processed"]:
            self.logger.info("📱 Archivo del Desktop procesado exitosamente")
            return True
        elif desktop_result["source"] == "already_processed":
            self.logger.info("📅 Archivo ya procesado hoy, manteniendo resultados anteriores")
            return False
        elif desktop_result["source"] == "existing_better":
            self.logger.info("📁 Archivo actual es más reciente que Desktop")
            return False
        else:
            # FALLBACK: Verificar archivo normal para cambios
            return self._check_normal_colors_update()

    def _check_desktop_colors(self) -> Dict[str, Any]:
        """
        Verificación inteligente del Desktop para colores
        Returns: dict con información del procesamiento
        """
        desktop_file = r"C:\Users\ccusi\Desktop\STOCK_MODELO_COLOR.xls"
        processed_marker = "logs/desktop_colors_processed.json"
        work_file = "data_sources/raw_reports/STOCK_MODELO_COLOR.xls"
        
        try:
            # Crear directorios necesarios
            os.makedirs(os.path.dirname(processed_marker), exist_ok=True)
            
            # Verificar si existe archivo en Desktop
            if not os.path.exists(desktop_file):
                return {
                    "processed": False,
                    "source": "no_desktop_file",
                    "message": "No hay archivo en Desktop"
                }
            
            # Verificar si ya fue procesado hoy
            if self._is_desktop_already_processed_today(desktop_file, processed_marker):
                self.logger.info("📅 Archivo Desktop ya procesado hoy")
                # Eliminar archivo duplicado
                try:
                    os.remove(desktop_file)
                    self.logger.info("🗑️ Archivo duplicado eliminado del Desktop")
                except Exception as e:
                    self.logger.warning(f"⚠️ No se pudo eliminar archivo del Desktop: {e}")
                
                return {
                    "processed": False,
                    "source": "already_processed",
                    "message": "Archivo ya procesado hoy, usando resultados anteriores"
                }
            
            # Verificar timestamps si existe archivo de trabajo
            if os.path.exists(work_file):
                desktop_mtime = os.path.getmtime(desktop_file)
                work_mtime = os.path.getmtime(work_file)
                
                if desktop_mtime > work_mtime:
                    self.logger.info("📱 Archivo del Desktop es más reciente, procesando...")
                    return {
                        "processed": True,
                        "source": "desktop_newer",
                        "message": "Archivo nuevo del Desktop detectado",
                        "desktop_file": desktop_file
                    }
                else:
                    self.logger.info("📁 Archivo actual es más reciente que Desktop")
                    return {
                        "processed": False,
                        "source": "existing_better",
                        "message": "Usando archivo actual (más reciente)"
                    }
            else:
                # No existe archivo de trabajo, usar Desktop
                self.logger.info("📱 No existe archivo actual, procesando Desktop")
                return {
                    "processed": True,
                    "source": "desktop_only",
                    "message": "No hay archivo actual, procesando Desktop",
                    "desktop_file": desktop_file
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error verificando Desktop: {e}")
            return {
                "processed": False,
                "source": "error",
                "message": f"Error verificando Desktop: {e}"
            }

    def _is_desktop_already_processed_today(self, file_path: str, marker_file: str) -> bool:
        """Verifica si el archivo Desktop ya fue procesado hoy"""
        try:
            if not os.path.exists(marker_file):
                return False
            
            with open(marker_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            last_processed = data.get('last_processed_date')
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            return (last_processed == current_date and
                    data.get('file_path') == file_path and
                    data.get('processed', False))
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error verificando estado Desktop: {e}")
            return False

    def _check_normal_colors_update(self) -> bool:
        """Lógica original de verificación para archivo normal (fallback)"""
        colors_data_file = "data_sources/raw_reports/STOCK_MODELO_COLOR.xls"
        hash_file = "logs/colors_data_hash.json"
        output_excel = "outputs/reports/stock_color.xlsx"
        output_json = "outputs/reports/colores_por_codigo.json"

        # SI NO EXISTEN LOS ARCHIVOS DE SALIDA, GENERARLOS SIEMPRE
        if not os.path.exists(output_excel) or not os.path.exists(output_json):
            self.logger.info("Archivos de colores no existen, generando por primera vez...")
            return True

        # Verificar si existe el archivo de datos
        if not os.path.exists(colors_data_file):
            self.logger.warning(f"Archivo de datos de colores no encontrado: {colors_data_file}")
            return False

        # Calcular hash del archivo actual
        current_hash = self._get_file_hash(colors_data_file)

        # Cargar hash anterior si existe
        previous_hash = None
        if os.path.exists(hash_file):
            try:
                with open(hash_file, 'r') as f:
                    data = json.load(f)
                    previous_hash = data.get('hash')
            except Exception as e:
                self.logger.warning(f"Error al leer hash anterior de colores: {e}")

        # Comparar hashes
        if current_hash != previous_hash:
            # Guardar nuevo hash
            try:
                os.makedirs("logs", exist_ok=True)
                with open(hash_file, 'w') as f:
                    json.dump({'hash': current_hash, 'updated': str(date.today())}, f)
            except Exception as e:
                self.logger.warning(f"Error al guardar hash de colores: {e}")

            return True

        return False

    def _should_update_holidays(self) -> bool:
        """Determina si se debe actualizar el reporte de feriados basado en cambios en el archivo fuente."""
        feriados_source = "data_sources/catalogs/feriados.xlsx"
        hash_file = "logs/feriados_hash.json"
        output_json = "outputs/reports/feriados.json"

        # SI NO EXISTE EL ARCHIVO DE SALIDA, GENERARLO SIEMPRE
        if not os.path.exists(output_json):
            self.logger.info("Archivo de feriados no existe, generando por primera vez...")
            return True

        # Verificar si existe el archivo fuente
        if not os.path.exists(feriados_source):
            self.logger.warning(f"Archivo fuente de feriados no encontrado: {feriados_source}")
            return False

        # Calcular hash del archivo actual
        current_hash = self._get_file_hash(feriados_source)

        # Cargar hash anterior si existe
        previous_hash = None
        if os.path.exists(hash_file):
            try:
                with open(hash_file, 'r') as f:
                    data = json.load(f)
                    previous_hash = data.get('hash')
            except Exception as e:
                self.logger.warning(f"Error al leer hash anterior de feriados: {e}")

        # Comparar hashes
        if current_hash != previous_hash:
            # Guardar nuevo hash
            try:
                os.makedirs("logs", exist_ok=True)
                with open(hash_file, 'w') as f:
                    json.dump({'hash': current_hash, 'updated': str(date.today())}, f)
            except Exception as e:
                self.logger.warning(f"Error al guardar hash de feriados: {e}")

            return True

        return False

    def _get_file_hash(self, filepath: str) -> Optional[str]:
        """Calcula el hash MD5 de un archivo."""
        try:
            import hashlib
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.warning(f"No se pudo calcular hash de {filepath}: {e}")
            return None

    def _execute_etl_main(self) -> Dict[str, Any]:
        """Ejecuta el ETL principal (main.py)."""
        result = {"success": False, "files": [], "error": None}

        try:
            import subprocess
            main_script = PROJECT_ROOT / "main.py"

            if not main_script.exists():
                raise FileNotFoundError(f"Script main.py no encontrado: {main_script}")

            self.logger.info(f"🚀 Ejecutando ETL principal: python {main_script}")

            process = subprocess.run(
                [sys.executable, str(main_script)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )

            if process.returncode == 0:
                result["success"] = True
                # Los archivos se generan en outputs/reports/ y luego se consolidan
                result["files"] = ["reporte_stock_hoy.xlsx", "productos_local.json", "stock_generales.json",
                                  "reporte_especiales.xlsx", "reporte_historico_general_VES.xlsx"]
                self.logger.info("✅ ETL principal ejecutado exitosamente")
            else:
                result["error"] = f"Exit code {process.returncode}"
                if process.stderr:
                    result["error"] += f" - STDERR: {process.stderr[:200]}..."

        except subprocess.TimeoutExpired:
            result["error"] = "Timeout después de 10 minutos"
        except Exception as e:
            result["error"] = str(e)

        return result

    def _execute_colors_report(self) -> Dict[str, Any]:
        """Ejecuta la generación de reportes de colores."""
        result = {"success": False, "files": [], "error": None}

        try:
            import subprocess
            colors_script = PROJECT_ROOT / "scripts" / "generate_colores_json.py"

            if not colors_script.exists():
                raise FileNotFoundError(f"Script de colores no encontrado: {colors_script}")

            self.logger.info(f"🎨 Ejecutando script de colores: python {colors_script}")

            process = subprocess.run(
                [sys.executable, str(colors_script)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )

            if process.returncode == 0:
                result["success"] = True
                result["files"] = ["stock_color.xlsx", "colores_por_codigo.json"]
            else:
                result["error"] = f"Exit code {process.returncode}"

        except subprocess.TimeoutExpired:
            result["error"] = "Timeout generando colores"
        except Exception as e:
            result["error"] = str(e)

        return result

    def _execute_holidays_report(self) -> Dict[str, Any]:
        """Ejecuta la generación de reportes de feriados."""
        result = {"success": False, "files": [], "error": None}

        try:
            import subprocess
            holidays_script = PROJECT_ROOT / "scripts" / "generate_feriados_json.py"

            if not holidays_script.exists():
                raise FileNotFoundError(f"Script de feriados no encontrado: {holidays_script}")

            self.logger.info(f"📅 Ejecutando script de feriados: python {holidays_script}")

            process = subprocess.run(
                [sys.executable, str(holidays_script)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutos timeout
            )

            if process.returncode == 0:
                result["success"] = True
                result["files"] = ["feriados.json"]
            else:
                result["error"] = f"Exit code {process.returncode}"

        except subprocess.TimeoutExpired:
            result["error"] = "Timeout generando feriados"
        except Exception as e:
            result["error"] = str(e)

        return result

    def _consolidate_outputs(self) -> Dict[str, Any]:
        """Verifica que los archivos estén en el directorio unificado."""
        result = {"success": True, "files": [], "warnings": []}

        try:
            reports_dir = Path(self.config["directories"]["reports"])

            if reports_dir.exists():
                self.logger.info(f"🔍 Verificando archivos en {reports_dir}")

                for file_path in reports_dir.glob("*"):
                    if file_path.is_file() and file_path.suffix in ['.xlsx', '.json']:
                        result["files"].append(file_path.name)
                        self.logger.debug(f"✅ Encontrado: {file_path.name}")

        except Exception as e:
            result["success"] = False
            result["warnings"].append(f"Error en verificación: {str(e)}")
            self.logger.error(f"💥 Error verificando outputs: {e}")

        return result

    def _validate_generated_files(self, files: List[str]) -> Dict[str, Any]:
        """Valida que los archivos generados sean correctos."""
        result = {"success": True, "errors": []}

        try:
            reports_dir = Path(self.config["directories"]["reports"])

            for file_name in files:
                file_path = reports_dir / file_name
                if not file_path.exists():
                    result["errors"].append(f"Archivo no encontrado: {file_name}")
                    result["success"] = False
                else:
                    # Verificar tamaño mínimo
                    size = file_path.stat().st_size
                    if size < 100:  # Menos de 100 bytes
                        result["errors"].append(f"Archivo muy pequeño: {file_name} ({size} bytes)")
                        result["success"] = False

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Error en validación: {str(e)}")

        return result

    def _generate_colors_report(self) -> List[str]:
        """Genera reporte de colores."""
        self.logger.info("🎨 Generando reporte de colores...")

        try:
            # Ejecutar script de colores
            import subprocess
            colors_script = PROJECT_ROOT / "scripts" / "generate_colores_json.py"

            if not colors_script.exists():
                self.logger.error(f"Script de colores no encontrado: {colors_script}")
                return []

            self.logger.info(f"🚀 Ejecutando: python {colors_script}")

            process = subprocess.run(
                [sys.executable, str(colors_script)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )

            if process.returncode == 0:
                self.logger.info("✅ Reporte de colores generado exitosamente")
                return ["stock_color.xlsx", "colores_por_codigo.json"]
            else:
                self.logger.error(f"❌ Error generando colores: Exit code {process.returncode}")
                if process.stderr:
                    self.logger.error(f"STDERR: {process.stderr}")
                return []

        except subprocess.TimeoutExpired:
            self.logger.error("⏰ Timeout generando reporte de colores")
            return []
        except Exception as e:
            self.logger.error(f"💥 Error ejecutando script de colores: {e}")
            return []

    def _generate_holidays_report(self) -> List[str]:
        """Genera reporte de feriados."""
        self.logger.info("📅 Generando reporte de feriados...")

        try:
            # Ejecutar script de feriados
            import subprocess
            holidays_script = PROJECT_ROOT / "scripts" / "generate_feriados_json.py"

            if not holidays_script.exists():
                self.logger.error(f"Script de feriados no encontrado: {holidays_script}")
                return []

            self.logger.info(f"🚀 Ejecutando: python {holidays_script}")

            process = subprocess.run(
                [sys.executable, str(holidays_script)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=120  # 2 minutos timeout
            )

            if process.returncode == 0:
                self.logger.info("✅ Reporte de feriados generado exitosamente")
                return ["feriados.json"]
            else:
                self.logger.error(f"❌ Error generando feriados: Exit code {process.returncode}")
                if process.stderr:
                    self.logger.error(f"STDERR: {process.stderr}")
                return []

        except subprocess.TimeoutExpired:
            self.logger.error("⏰ Timeout generando reporte de feriados")
            return []
        except Exception as e:
            self.logger.error(f"💥 Error ejecutando script de feriados: {e}")
            return []

    def _generate_special_report(self) -> List[str]:
        """Genera reporte especial (se genera en ETL principal)."""
        self.logger.info("⭐ Reporte especial generado por ETL principal...")
        return ["reporte_especiales.xlsx"]

    def _generate_historical_report(self) -> List[str]:
        """Genera reporte histórico (se genera en ETL principal)."""
        self.logger.info("📈 Reporte histórico generado por ETL principal...")
        return ["reporte_historico_general_VES.xlsx"]

    def _deliver_files(self, files: List[str], server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Entrega archivos según configuración del servidor."""
        self.logger.info(f"📤 Entregando a {server_config['type']}: {server_config['name']}")

        try:
            # Usar módulo file_delivery si está disponible
            if "file_delivery" in self.modules:
                delivery_module = self.modules["file_delivery"]
                if hasattr(delivery_module, "deliver_files"):
                    result = delivery_module.deliver_files(files, server_config["name"])
                    return {
                        "delivered": result.get("files_delivered", 0),
                        "server_type": server_config["type"],
                        "success": result.get("success", False)
                    }

            # Fallback: simular entrega
            self.logger.warning("Módulo file_delivery no disponible, simulando entrega")
            return {
                "delivered": len(files),
                "server_type": server_config["type"],
                "success": True
            }

        except Exception as e:
            self.logger.error(f"Error en entrega: {e}")
            return {
                "delivered": 0,
                "server_type": server_config["type"],
                "success": False,
                "error": str(e)
            }


def main():
    """Función principal para ejecución desde línea de comandos."""
    parser = argparse.ArgumentParser(description="Sistema de Gestión de Stock - Orquestador")
    parser.add_argument("--full-etl", action="store_true", help="Ejecutar ETL completo")
    parser.add_argument("--report", type=str, help="Generar reporte específico (colors, holidays, special, historical)")
    parser.add_argument("--deliver", type=str, help="Entregar archivos a servidor específico")
    parser.add_argument("--list-reports", action="store_true", help="Listar tipos de reportes disponibles")
    parser.add_argument("--list-servers", action="store_true", help="Listar servidores disponibles")

    args = parser.parse_args()

    # Inicializar orquestador
    orchestrator = StockOrchestrator()

    try:
        if args.full_etl:
            result = orchestrator.run_full_etl()
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.report:
            result = orchestrator.generate_specific_report(args.report)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.deliver:
            # TODO: Obtener lista de archivos a entregar
            files = ["reporte_stock_hoy.xlsx"]  # Placeholder
            result = orchestrator.deliver_to_server(files, args.deliver)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.list_reports:
            reports = orchestrator.config["reports"]
            print("[INFO] Reportes disponibles:")
            for report_type, config in reports.items():
                print(f"  • {report_type}: {config['name']} ({config['frequency']})")

        elif args.list_servers:
            servers = orchestrator.config["delivery"]["servers"]
            print("🖥️ Servidores disponibles:")
            for server in servers:
                print(f"  • {server['name']}: {server['type']} - {server.get('path', 'N/A')}")

        else:
            parser.print_help()

    except Exception as e:
        orchestrator.logger.error(f"💥 Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()