#!/usr/bin/env python3
"""
Script principal que ejecuta el proceso ETL completo incluyendo:
- ETL principal (main.py)
- Generación de feriados (solo si hay cambios)
- Generación de stock de colores (diario)
- Reportes especiales

Frecuencias de actualización:
- ETL principal: Cada vez que se ejecuta
- Stock de colores: Una vez al día
- Feriados: Solo cuando hay cambios en el archivo fuente
"""

import os
import sys
import subprocess
import logging
import hashlib
import json
from datetime import datetime, date
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """Configura el sistema de logging."""
    # Usar ruta absoluta desde la raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, "logs")
    log_filename = f"proceso_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = os.path.join(logs_dir, log_filename)

    # Crear directorio logs si no existe
    os.makedirs(logs_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler()
        ],
    )
    return logging.getLogger(__name__)

def get_file_hash(filepath):
    """Calcula el hash MD5 de un archivo para detectar cambios."""
    try:
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logging.warning(f"No se pudo calcular hash de {filepath}: {e}")
        return None

def should_update_feriados():
    """Determina si se debe actualizar el archivo de feriados."""
    # Usar ruta absoluta desde la raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    feriados_source = os.path.join(project_root, "data_sources", "catalogs", "feriados.xlsx")
    hash_file = os.path.join(project_root, "logs", "feriados_hash.json")

    # Verificar si existe el archivo fuente
    if not os.path.exists(feriados_source):
        logging.warning(f"Archivo fuente de feriados no encontrado: {feriados_source}")
        return False

    # Calcular hash del archivo actual
    current_hash = get_file_hash(feriados_source)

    # Cargar hash anterior si existe
    previous_hash = None
    if os.path.exists(hash_file):
        try:
            with open(hash_file, 'r') as f:
                data = json.load(f)
                previous_hash = data.get('hash')
        except Exception as e:
            logging.warning(f"Error al leer hash anterior: {e}")

    # Comparar hashes
    if current_hash != previous_hash:
        # Guardar nuevo hash
        try:
            with open(hash_file, 'w') as f:
                json.dump({'hash': current_hash, 'updated': str(date.today())}, f)
        except Exception as e:
            logging.warning(f"Error al guardar hash: {e}")

        return True

    return False

def should_update_colores():
    """Determina si se debe actualizar el archivo de colores (diario)."""
    today = str(date.today())
    # Usar ruta absoluta desde la raíz del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    last_update_file = os.path.join(project_root, "logs", "colores_last_update.json")

    # Verificar última actualización
    try:
        if os.path.exists(last_update_file):
            with open(last_update_file, 'r') as f:
                data = json.load(f)
                last_update = data.get('last_update')

                if last_update == today:
                    logging.info("Stock de colores ya actualizado hoy, omitiendo...")
                    return False
    except Exception as e:
        logging.warning(f"Error al verificar última actualización de colores: {e}")

    # Actualizar fecha de última actualización
    try:
        with open(last_update_file, 'w') as f:
            json.dump({'last_update': today}, f)
    except Exception as e:
        logging.warning(f"Error al guardar fecha de actualización: {e}")

    return True

def run_etl_principal():
    """Ejecuta el ETL principal."""
    logging.info("=== EJECUTANDO ETL PRINCIPAL ===")

    try:
        # Ejecutar main.py desde la raíz del proyecto
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = subprocess.run([sys.executable, "main.py"],
                              capture_output=True, text=True, cwd=project_root)

        if result.returncode == 0:
            logging.info("✅ ETL principal ejecutado exitosamente")
            logging.info(result.stdout)
        else:
            logging.error("❌ Error en ETL principal:")
            logging.error(result.stderr)
            return False

        return True

    except Exception as e:
        logging.error(f"❌ Error al ejecutar ETL principal: {e}")
        return False

def run_generate_feriados():
    """Ejecuta la generación de feriados si hay cambios."""
    logging.info("=== VERIFICANDO ACTUALIZACIÓN DE FERIADOS ===")

    if should_update_feriados():
        logging.info("📅 Cambios detectados en feriados, actualizando...")

        try:
            # Ejecutar desde la raíz del proyecto
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run([sys.executable, "scripts/generate_feriados_json.py"],
                                  capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                logging.info("✅ Feriados actualizados exitosamente")
                logging.info(result.stdout)
            else:
                logging.error("❌ Error al actualizar feriados:")
                logging.error(result.stderr)
                return False

        except Exception as e:
            logging.error(f"❌ Error al ejecutar actualización de feriados: {e}")
            return False
    else:
        logging.info("📅 No hay cambios en feriados, omitiendo actualización")

    return True

def run_generate_colores():
    """Ejecuta la generación de stock de colores."""
    logging.info("=== VERIFICANDO ACTUALIZACIÓN DE COLORES ===")

    if should_update_colores():
        logging.info("🎨 Actualizando stock de colores...")

        try:
            # Ejecutar desde la raíz del proyecto
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            result = subprocess.run([sys.executable, "scripts/generate_colores_json.py"],
                                  capture_output=True, text=True, cwd=project_root)

            if result.returncode == 0:
                logging.info("✅ Stock de colores actualizado exitosamente")
                logging.info(result.stdout)
            else:
                logging.error("❌ Error al actualizar stock de colores:")
                logging.error(result.stderr)
                return False

        except Exception as e:
            logging.error(f"❌ Error al ejecutar actualización de colores: {e}")
            return False
    else:
        logging.info("🎨 Stock de colores ya actualizado hoy")

    return True

def main():
    """Función principal que ejecuta todos los procesos."""
    logger = setup_logging()
    logger.info("🚀 === INICIANDO PROCESO COMPLETO DE ETL ===")

    success = True

    # 1. Ejecutar ETL principal
    if not run_etl_principal():
        success = False

    # 2. Actualizar feriados (solo si hay cambios)
    if not run_generate_feriados():
        success = False

    # 3. Actualizar stock de colores (diario)
    if not run_generate_colores():
        success = False

    # Resumen final
    if success:
        logger.info("✅ === PROCESO COMPLETO EJECUTADO EXITOSAMENTE ===")
        logger.info("📊 Reportes generados:")
        logger.info("  - reporte_stock_hoy.xlsx")
        logger.info("  - reporte_historico_general_VES.xlsx")
        logger.info("  - reporte_especiales.xlsx")
        logger.info("  - productos_local.json")
        logger.info("  - stock_generales.json")
        logger.info("  - feriados.json (si hubo cambios)")
        logger.info("  - stock_color.xlsx (diario)")
        logger.info("  - colores_por_codigo.json (diario)")
    else:
        logger.error("❌ === PROCESO COMPLETO FALLÓ ===")
        logger.error("🔧 Revisa los logs para más detalles")

    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logging.info("⏹️ Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        logging.error(f"💥 Error fatal: {e}")
        sys.exit(1)