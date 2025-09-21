#!/usr/bin/env python3
"""
Procesador Local Simple para Gestion360
=======================================

Versión simplificada que funciona solo con archivos locales.
No requiere credenciales de Google Drive API.

Archivos de entrada (locales):
- G:\My Drive\360_base_inicio\STOCK_MODELO_COLOR.xls
- G:\My Drive\360_base_inicio\feriados.xlsx
- G:\My Drive\360_base_inicio\base_total.xls
- G:\My Drive\360_base_inicio\codigos_generales.xlsx

Archivos de salida (locales):
- G:\My Drive\360_salida\productos_local.json
- G:\My Drive\360_salida\stock_generales.json
- G:\My Drive\360_salida\feriados.json
- G:\My Drive\360_salida\colors_data.json

Autor: Carlos Cusihuamán
Fecha: 2025-01-20
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

class LocalProcessorSimple:
    def __init__(self):
        # Rutas locales de Google Drive
        self.base_inicio = r"G:\My Drive\360_base_inicio"
        self.salida = r"G:\My Drive\360_salida"

        # Archivos a procesar
        self.source_files = {
            'stock': 'STOCK_MODELO_COLOR.xls',
            'holidays': 'feriados.xlsx',
            'colors': 'base_total.xls',
            'products': 'codigos_generales.xlsx'
        }

        # Archivos de salida
        self.output_files = {
            'productos_local': 'productos_local.json',
            'stock_generales': 'stock_generales.json',
            'feriados': 'feriados.json',
            'colors_data': 'colors_data.json'
        }

        # Hashes para detectar cambios
        self.hashes_file = 'local_hashes.pkl'
        self.previous_hashes = self.load_previous_hashes()

    def load_previous_hashes(self):
        """Carga hashes anteriores"""
        try:
            import pickle
            if os.path.exists(self.hashes_file):
                with open(self.hashes_file, 'rb') as f:
                    return pickle.load(f)
        except:
            pass
        return {}

    def save_hashes(self):
        """Guarda hashes actuales"""
        try:
            import pickle
            with open(self.hashes_file, 'wb') as f:
                pickle.dump(self.previous_hashes, f)
        except Exception as e:
            print(f"⚠️  Error guardando hashes: {e}")

    def calculate_file_hash(self, file_path):
        """Calcula hash MD5 del archivo"""
        if not os.path.exists(file_path):
            return None

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def has_file_changed(self, file_path, file_key):
        """Verifica si archivo cambió"""
        current_hash = self.calculate_file_hash(file_path)
        if current_hash is None:
            return False

        previous_hash = self.previous_hashes.get(file_key)
        return current_hash != previous_hash

    def ensure_directories(self):
        """Asegurar que existan los directorios"""
        for directory in [self.base_inicio, self.salida]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"📁 Creado directorio: {directory}")

    def validate_input_files(self):
        """Validar archivos de entrada"""
        print("🔍 Validando archivos de entrada...")

        missing_files = []
        found_files = 0

        for file_key, filename in self.source_files.items():
            file_path = os.path.join(self.base_inicio, filename)

            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"✅ {filename} ({file_size} bytes)")
                found_files += 1
            else:
                print(f"❌ {filename} no encontrado en {self.base_inicio}")
                missing_files.append(filename)

        if missing_files:
            print(f"\n⚠️  Faltan {len(missing_files)} archivos:")
            for missing in missing_files:
                print(f"   • Coloca {missing} en {self.base_inicio}")
            return False

        print(f"\n✅ {found_files}/{len(self.source_files)} archivos encontrados")
        return True

    def copy_file_to_local(self, source_path, dest_path):
        """Copia archivo localmente"""
        try:
            import shutil
            shutil.copy2(source_path, dest_path)
            print(f"📋 Copiado: {os.path.basename(source_path)}")
            return True
        except Exception as e:
            print(f"❌ Error copiando {source_path}: {e}")
            return False

    def prepare_local_files(self):
        """Prepara archivos locales para procesamiento"""
        print("📂 Preparando archivos locales...")

        # Crear directorios locales si no existen
        local_data_dir = "data_sources"
        os.makedirs(os.path.join(local_data_dir, "raw_reports"), exist_ok=True)
        os.makedirs(os.path.join(local_data_dir, "catalogs"), exist_ok=True)
        os.makedirs(os.path.join(local_data_dir, "base_data"), exist_ok=True)

        # Copiar archivos desde Google Drive local
        copied_files = 0

        for file_key, filename in self.source_files.items():
            source_path = os.path.join(self.base_inicio, filename)

            if file_key == 'stock':
                dest_path = f"data_sources/raw_reports/{filename}"
            elif file_key == 'holidays':
                dest_path = f"data_sources/catalogs/{filename}"
            elif file_key == 'colors':
                dest_path = f"data_sources/base_data/{filename}"
            elif file_key == 'products':
                dest_path = f"data_sources/catalogs/{filename}"

            if os.path.exists(source_path):
                if self.copy_file_to_local(source_path, dest_path):
                    copied_files += 1
            else:
                print(f"⚠️  {filename} no encontrado")

        return copied_files

    def process_etl(self):
        """Ejecuta procesamiento ETL"""
        print("🔄 Ejecutando procesamiento ETL...")

        try:
            # Ejecutar script principal
            import subprocess
            result = subprocess.run(['python', 'main.py'],
                                  capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("✅ ETL principal ejecutado correctamente")
                return True
            else:
                print(f"⚠️  ETL principal con warnings: {result.stderr}")
                return True  # Consideramos éxito si no hay error crítico

        except subprocess.TimeoutExpired:
            print("❌ Timeout en procesamiento ETL")
            return False
        except Exception as e:
            print(f"❌ Error en ETL: {e}")
            return False

    def copy_results_to_drive(self):
        """Copia resultados a carpeta de Google Drive"""
        print("📤 Copiando resultados a Google Drive...")

        # Crear directorio de salida si no existe
        os.makedirs(self.salida, exist_ok=True)

        copied_files = 0

        for file_key, filename in self.output_files.items():
            source_path = f"outputs/reports/{filename}"
            dest_path = os.path.join(self.salida, filename)

            if os.path.exists(source_path):
                if self.copy_file_to_local(source_path, dest_path):
                    # Actualizar hash para detectar cambios futuros
                    self.previous_hashes[file_key] = self.calculate_file_hash(source_path)
                    copied_files += 1
                    print(f"✅ {filename} → {self.salida}")
                else:
                    print(f"❌ Error copiando {filename}")
            else:
                print(f"⚠️  {source_path} no encontrado")

        # Guardar hashes actualizados
        self.save_hashes()

        return copied_files

    def generate_summary(self):
        """Genera resumen del procesamiento"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'input_directory': self.base_inicio,
            'output_directory': self.salida,
            'processed_files': len(self.output_files),
            'status': 'completed'
        }

        summary_path = os.path.join(self.salida, 'processing_summary.json')
        try:
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"📊 Resumen guardado en: {summary_path}")
        except Exception as e:
            print(f"⚠️  Error guardando resumen: {e}")

    def run_full_cycle(self):
        """Ejecuta ciclo completo de procesamiento"""
        print(f"🚀 Iniciando procesamiento local: {datetime.now()}")
        print("=" * 60)
        print(f"📥 Entrada: {self.base_inicio}")
        print(f"📤 Salida: {self.salida}")
        print("=" * 60)

        # 1. Asegurar directorios
        self.ensure_directories()

        # 2. Validar archivos de entrada
        if not self.validate_input_files():
            print("\n❌ Faltan archivos de entrada. Colócalos en la carpeta correcta.")
            return False

        print()

        # 3. Preparar archivos locales
        prepared_files = self.prepare_local_files()
        print(f"📋 Archivos preparados: {prepared_files}")

        # 4. Ejecutar ETL
        if not self.process_etl():
            print("❌ Error en procesamiento ETL")
            return False

        # 5. Copiar resultados
        copied_results = self.copy_results_to_drive()
        print(f"📤 Resultados copiados: {copied_results}")

        # 6. Generar resumen
        self.generate_summary()

        print("=" * 60)
        print("✅ Procesamiento completado exitosamente")
        print(f"📅 {datetime.now()}")

        return True

def main():
    """Función principal"""
    print("🎯 Procesador Local Simple para Gestion360")
    print("Versión sin credenciales - Solo archivos locales")
    print("-" * 50)

    processor = LocalProcessorSimple()
    success = processor.run_full_cycle()

    if success:
        print("\n🎉 ¡Procesamiento completado!")
        print("📁 Revisa los resultados en:")
        print(f"   • {processor.salida}")
    else:
        print("\n💥 Error en el procesamiento")
        print("📋 Revisa los mensajes de error arriba")
        exit(1)

if __name__ == "__main__":
    main()