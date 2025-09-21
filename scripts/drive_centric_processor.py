#!/usr/bin/env python3
"""
Drive-Centric Processor para Gestion360
=======================================

Este script centraliza todo el procesamiento ETL usando Google Drive:

1. Descarga archivos fuente desde G:\My Drive\360_base_inicio
2. Ejecuta procesamiento ETL local
3. Guarda resultados en G:\My Drive\360_salida
4. Sube archivos finales a carpeta compartida para Google Cloud

Autor: Carlos Cusihuamán
Fecha: 2025-01-20
"""

import os
import json
import pickle
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

# Google Drive API
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

class DriveCentricProcessor:
    def __init__(self):
        # Rutas de Google Drive
        self.base_inicio_path = r"G:\My Drive\360_base_inicio"
        self.salida_path = r"G:\My Drive\360_salida"
        self.cloud_folder_id = '1c3Hk00HDmtCFEfZOxR4U6jGK44Ngb3hu'  # Carpeta compartida

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
        self.hashes_file = 'drive_hashes.pkl'
        self.previous_hashes = self.load_previous_hashes()

        # Autenticación Drive
        self.creds = self.authenticate_drive()
        if self.creds:
            self.service = build('drive', 'v3', credentials=self.creds)

    def authenticate_drive(self):
        """Autenticación con Google Drive"""
        creds = None

        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                print("❌ Error: Configura autenticación con 'python scripts/setup_drive_auth.py'")
                return None

        return creds

    def calculate_file_hash(self, file_path):
        """Calcula hash MD5 del archivo"""
        if not os.path.exists(file_path):
            return None

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def load_previous_hashes(self):
        """Carga hashes anteriores"""
        if os.path.exists(self.hashes_file):
            try:
                with open(self.hashes_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return {}

    def save_hashes(self):
        """Guarda hashes actuales"""
        with open(self.hashes_file, 'wb') as f:
            pickle.dump(self.previous_hashes, f)

    def download_from_drive(self, drive_path, local_path):
        """Descarga archivo desde Google Drive"""
        try:
            # Buscar archivo en Drive
            results = self.service.files().list(
                q=f"name='{os.path.basename(drive_path)}' and trashed=false",
                fields="files(id, name)"
            ).execute()

            if not results.get('files'):
                print(f"⚠️  Archivo no encontrado en Drive: {drive_path}")
                return False

            file_id = results['files'][0]['id']

            # Descargar archivo
            request = self.service.files().get_media(fileId=file_id)

            with open(local_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()

            print(f"📥 Descargado: {drive_path} → {local_path}")
            return True

        except Exception as e:
            print(f"❌ Error descargando {drive_path}: {e}")
            return False

    def upload_to_drive(self, local_path, drive_filename, target_folder=None):
        """Sube archivo a Google Drive"""
        try:
            folder_id = target_folder or self.cloud_folder_id

            file_metadata = {
                'name': drive_filename,
                'parents': [folder_id]
            }

            media = MediaFileUpload(local_path, resumable=True)

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            print(f"☁️  Subido: {drive_filename} (ID: {file.get('id')})")
            return True

        except Exception as e:
            print(f"❌ Error subiendo {drive_filename}: {e}")
            return False

    def has_file_changed(self, file_path, file_key):
        """Verifica si archivo cambió"""
        current_hash = self.calculate_file_hash(file_path)
        if current_hash is None:
            return False

        previous_hash = self.previous_hashes.get(file_key)
        return current_hash != previous_hash

    def sync_source_files(self):
        """Sincroniza archivos fuente desde 360_base_inicio"""
        print("📥 Sincronizando archivos fuente...")

        synced_files = 0

        for file_key, filename in self.source_files.items():
            drive_path = f"360_base_inicio/{filename}"
            local_path = f"data_sources/{filename}"

            # Asegurar que existe el directorio local
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            if self.download_from_drive(drive_path, local_path):
                synced_files += 1
                print(f"✅ {filename} sincronizado")
            else:
                print(f"❌ Error sincronizando {filename}")

        return synced_files

    def process_etl(self):
        """Ejecuta el procesamiento ETL"""
        print("🔄 Ejecutando procesamiento ETL...")

        try:
            # Ejecutar script principal
            result = subprocess.run(['python', 'main.py'],
                                  capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("✅ ETL principal ejecutado correctamente")
            else:
                print(f"⚠️  ETL principal con warnings: {result.stderr}")

            # Generar feriados si es necesario
            if os.path.exists('data_sources/catalogs/feriados.xlsx'):
                result2 = subprocess.run(['python', 'scripts/generate_feriados_json.py'],
                                       capture_output=True, text=True, timeout=60)

                if result2.returncode == 0:
                    print("✅ Feriados generados correctamente")
                else:
                    print(f"⚠️  Error generando feriados: {result2.stderr}")

            return True

        except subprocess.TimeoutExpired:
            print("❌ Timeout en procesamiento ETL")
            return False
        except Exception as e:
            print(f"❌ Error en ETL: {e}")
            return False

    def sync_output_files(self):
        """Sincroniza archivos de salida a 360_salida"""
        print("📤 Sincronizando archivos de salida...")

        synced_files = 0

        for file_key, filename in self.output_files.items():
            local_path = f"outputs/{filename}"

            if os.path.exists(local_path):
                # Crear nombre para Drive
                drive_filename = f"{file_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                if self.upload_to_drive(local_path, drive_filename):
                    synced_files += 1
                    print(f"✅ {filename} subido a 360_salida")
                else:
                    print(f"❌ Error subiendo {filename}")
            else:
                print(f"⚠️  {local_path} no encontrado")

        return synced_files

    def upload_to_cloud(self):
        """Sube archivos finales a carpeta compartida para Google Cloud"""
        print("☁️  Subiendo archivos a Google Cloud...")

        uploaded_files = 0

        for file_key, filename in self.output_files.items():
            local_path = f"outputs/{filename}"

            if os.path.exists(local_path):
                # Verificar si cambió (excepto productos_local y stock_generales que siempre se suben)
                should_upload = True
                if file_key in ['feriados', 'colors_data']:
                    should_upload = self.has_file_changed(local_path, file_key)

                if should_upload:
                    drive_filename = f"{file_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

                    if self.upload_to_drive(local_path, drive_filename):
                        # Actualizar hash
                        self.previous_hashes[file_key] = self.calculate_file_hash(local_path)
                        uploaded_files += 1
                        print(f"🚀 {filename} → Cloud")
                    else:
                        print(f"❌ Error subiendo {filename} a cloud")
                else:
                    print(f"⏭️  {filename} sin cambios")
            else:
                print(f"⚠️  {local_path} no encontrado")

        # Guardar hashes actualizados
        self.save_hashes()

        return uploaded_files

    def run_full_cycle(self):
        """Ejecuta el ciclo completo de procesamiento"""
        print(f"🚀 Iniciando ciclo completo: {datetime.now()}")
        print("=" * 60)

        if not self.creds:
            print("❌ Error de autenticación. Configura Drive primero.")
            return False

        try:
            # 1. Sincronizar archivos fuente
            source_synced = self.sync_source_files()
            print(f"📊 Archivos fuente sincronizados: {source_synced}")

            # 2. Ejecutar ETL
            if not self.process_etl():
                print("❌ ETL falló, abortando ciclo")
                return False

            # 3. Sincronizar archivos de salida
            output_synced = self.sync_output_files()
            print(f"📤 Archivos de salida sincronizados: {output_synced}")

            # 4. Subir a Google Cloud
            cloud_uploaded = self.upload_to_cloud()
            print(f"☁️  Archivos subidos a cloud: {cloud_uploaded}")

            print("=" * 60)
            print("✅ Ciclo completo finalizado exitosamente")
            print(f"📅 {datetime.now()}")

            return True

        except Exception as e:
            print(f"❌ Error en ciclo completo: {e}")
            return False

def main():
    """Función principal"""
    print("🎯 Drive-Centric Processor para Gestion360")
    print("📍 Fuentes: G:\\My Drive\\360_base_inicio")
    print("📤 Salidas: G:\\My Drive\\360_salida")
    print("☁️  Cloud: Carpeta compartida")
    print("-" * 50)

    processor = DriveCentricProcessor()
    success = processor.run_full_cycle()

    if success:
        print("🎉 Procesamiento completado exitosamente")
    else:
        print("💥 Error en el procesamiento")
        exit(1)

if __name__ == "__main__":
    main()