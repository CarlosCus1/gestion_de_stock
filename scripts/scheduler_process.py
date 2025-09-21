#!/usr/bin/env python3
"""
Scheduler para ejecutar el proceso ETL cada hora en horario laboral.
- Horario: Lunes a Sábado de 7:00 a 23:00
- Frecuencia: Cada hora
- Solo ejecuta si está en horario laboral
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime, timedelta
import json

def is_business_hours():
    """Verifica si es horario laboral (7:00-23:00)."""
    now = datetime.now()
    current_hour = now.hour

    # Horario laboral: 7:00 - 23:00
    return 7 <= current_hour <= 23

def is_business_day():
    """Verifica si es día laboral (lunes=0 a sábado=5)."""
    now = datetime.now()
    # Monday=0, Sunday=6
    return now.weekday() <= 5  # 0-5 = Monday-Saturday

def should_run_process():
    """Determina si se debe ejecutar el proceso."""
    return is_business_day() and is_business_hours()

def setup_logging():
    """Configura el sistema de logging."""
    log_filename = f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
    log_filepath = os.path.join("logs", log_filename)

    # Crear directorio logs si no existe
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filepath, encoding='utf-8'),
            logging.StreamHandler()
        ],
    )
    return logging.getLogger(__name__)

def load_execution_stats():
    """Carga estadísticas de ejecución."""
    stats_file = "logs/execution_stats.json"
    try:
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logging.warning(f"Error al cargar estadísticas: {e}")

    return {
        "total_executions": 0,
        "successful_executions": 0,
        "failed_executions": 0,
        "last_execution": None,
        "last_success": None,
        "daily_count": {}
    }

def save_execution_stats(stats):
    """Guarda estadísticas de ejecución."""
    stats_file = "logs/execution_stats.json"
    try:
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
    except Exception as e:
        logging.error(f"Error al guardar estadísticas: {e}")

def update_stats(stats, success=True):
    """Actualiza estadísticas de ejecución."""
    stats["total_executions"] += 1
    if success:
        stats["successful_executions"] += 1
        stats["last_success"] = datetime.now().isoformat()
    else:
        stats["failed_executions"] += 1

    stats["last_execution"] = datetime.now().isoformat()

    # Actualizar contador diario
    today = datetime.now().strftime('%Y-%m-%d')
    if today not in stats["daily_count"]:
        stats["daily_count"][today] = 0
    stats["daily_count"][today] += 1

    return stats

def run_etl_process():
    """Ejecuta el proceso ETL completo."""
    logging.info("🚀 === EJECUTANDO PROCESO ETL PROGRAMADO ===")

    try:
        # Ejecutar el proceso completo
        result = subprocess.run([sys.executable, "scripts/run_complete_process.py"],
                              capture_output=True, text=True, cwd=".")

        if result.returncode == 0:
            logging.info("✅ Proceso ETL ejecutado exitosamente")
            return True, result.stdout
        else:
            logging.error("❌ Error en proceso ETL:")
            logging.error(result.stderr)
            return False, result.stderr

    except Exception as e:
        logging.error(f"❌ Error al ejecutar proceso ETL: {e}")
        return False, str(e)

def wait_next_hour():
    """Espera hasta la próxima hora."""
    now = datetime.now()
    next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    wait_seconds = (next_hour - now).total_seconds()

    logging.info(f"⏰ Esperando hasta {next_hour.strftime('%H:%M')} ({wait_seconds:.0f} segundos)")
    time.sleep(wait_seconds)

def main():
    """Función principal del scheduler."""
    logger = setup_logging()
    logger.info("📅 === INICIANDO SCHEDULER ETL ===")
    logger.info("⏰ Configuración: Cada hora en horario laboral (7:00-23:00, Lun-Sáb)")

    stats = load_execution_stats()

    try:
        while True:
            current_time = datetime.now()

            # Verificar si es horario de ejecución
            if should_run_process():
                logger.info(f"🎯 {current_time.strftime('%Y-%m-%d %H:%M:%S')} - Ejecutando proceso programado")

                # Ejecutar proceso
                success, output = run_etl_process()

                # Actualizar estadísticas
                stats = update_stats(stats, success)

                # Log del resultado
                if success:
                    logger.info("✅ Proceso completado exitosamente")
                else:
                    logger.error("❌ Proceso falló")

                # Guardar estadísticas
                save_execution_stats(stats)

                # Log de estadísticas
                logger.info(f"📊 Estadísticas: {stats['successful_executions']}/{stats['total_executions']} exitosos")

            else:
                reason = []
                if not is_business_day():
                    reason.append("fuera de días laborables")
                if not is_business_hours():
                    reason.append("fuera de horario laboral")

                logger.info(f"⏸️ {current_time.strftime('%H:%M')} - No es horario de ejecución ({', '.join(reason)})")

            # Esperar hasta la próxima hora
            wait_next_hour()

    except KeyboardInterrupt:
        logger.info("⏹️ Scheduler detenido por el usuario")
    except Exception as e:
        logger.error(f"💥 Error fatal en scheduler: {e}")
        save_execution_stats(stats)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)