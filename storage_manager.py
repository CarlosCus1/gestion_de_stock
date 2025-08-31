import os
import logging
from google.cloud import storage
from google.oauth2 import service_account
from config import STORAGE_BUCKET_NAME, STORAGE_CREDENTIALS_PATH
from utils import validate_file_exists, format_file_size

class CloudStorageManager:
    def __init__(self):
        self.bucket_name = STORAGE_BUCKET_NAME
        self.credentials = None
        self.client = None
        self.bucket = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            if not os.path.exists(STORAGE_CREDENTIALS_PATH):
                logging.error(f"Archivo de credenciales no encontrado: {STORAGE_CREDENTIALS_PATH}")
                raise FileNotFoundError(f"Archivo de credenciales no encontrado: {STORAGE_CREDENTIALS_PATH}")
            self.credentials = service_account.Credentials.from_service_account_file(STORAGE_CREDENTIALS_PATH)
            self.client = storage.Client(credentials=self.credentials)
            self.bucket = self.client.bucket(self.bucket_name)
            logging.info(f"Cliente de Google Cloud Storage inicializado para bucket: {self.bucket_name}")
        except Exception as e:
            logging.error(f"Error inicializando cliente de Google Cloud Storage: {e}")

    def upload_file(self, local_path, blob_name, make_public=True):
        try:
            if not validate_file_exists(local_path, "archivo local"):
                return None
            blob = self.bucket.blob(blob_name)
            blob.upload_from_filename(local_path)
            logging.info(f"Archivo {local_path} subido como {blob_name}")
            if make_public:
                blob.make_public()
                logging.info(f"Archivo {blob_name} hecho público")
            return blob.public_url
        except Exception as e:
            logging.error(f"Error subiendo archivo a Google Cloud Storage: {e}")
            return None

    def generate_signed_url(self, blob_name, expiration_minutes=30):
        try:
            blob = self.bucket.blob(blob_name)
            url = blob.generate_signed_url(
                version="v4",
                expiration=expiration_minutes * 60,
                method="GET"
            )
            logging.info(f"URL firmada generada para {blob_name} (expira en {expiration_minutes} minutos)")
            return url
        except Exception as e:
            logging.error(f"Error generando URL firmada para {blob_name}: {e}")
            return None

    def file_exists(self, blob_name):
        try:
            blob = self.bucket.blob(blob_name)
            return blob.exists()
        except Exception as e:
            logging.error(f"Error verificando existencia de {blob_name}: {e}")
            return False

    def get_public_url(self, blob_name):
        try:
            if self.file_exists(blob_name):
                blob = self.bucket.blob(blob_name)
                return blob.public_url
            return None
        except Exception as e:
            logging.error(f"Error obteniendo URL pública de {blob_name}: {e}")
            return None

    def get_file_metadata(self, blob_name):
        try:
            blob = self.bucket.blob(blob_name)
            if not blob.exists():
                return None
            blob.reload()
            return {
                "name": blob.name,
                "size": blob.size,
                "size_formatted": format_file_size(blob.size) if blob.size else "0B",
                "content_type": blob.content_type,
                "time_created": blob.time_created,
                "updated": blob.updated,
                "etag": blob.etag,
                "md5_hash": blob.md5_hash,
                "crc32c": blob.crc32c
            }
        except Exception as e:
            logging.error(f"Error obteniendo metadatos de {blob_name}: {e}")
            return None

    def list_files(self, prefix=""):
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            files = []
            for blob in blobs:
                files.append({
                    "name": blob.name,
                    "size": blob.size,
                    "size_formatted": format_file_size(blob.size) if blob.size else "0B",
                    "time_created": blob.time_created,
                    "updated": blob.updated
                })
            return files
        except Exception as e:
            logging.error(f"Error listando archivos con prefijo '{prefix}': {e}")
            return []