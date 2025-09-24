#!/usr/bin/env python3
"""
Sistema de Entrega de Archivos - Sistema de Gestión de Stock

Este módulo maneja la entrega de archivos generados a diferentes destinos:
- Servidores locales
- Servidores en red (SMB/Windows shares)
- Servicios cloud (S3, etc.)
- FTP/SFTP
- API endpoints

Configuración centralizada en unified_config.json
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

# Configuración del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class FileDelivery:
    """
    Sistema unificado de entrega de archivos.
    """

    def __init__(self):
        self.logger = logging.getLogger("FileDelivery")
        self.config = self._load_delivery_config()

    def _load_delivery_config(self) -> Dict[str, Any]:
        """Carga configuración de entrega desde unified_config.json."""
        config_path = PROJECT_ROOT / "config" / "unified_config.json"

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    full_config = json.load(f)
                return full_config.get("delivery", {})
            except Exception as e:
                self.logger.error(f"Error cargando configuración de entrega: {e}")

        # Configuración por defecto
        return {
            "default_behavior": "auto",
            "servers": [
                {
                    "name": "local_desktop",
                    "type": "local",
                    "path": "C:\\Users\\{username}\\Desktop",
                    "enabled": True
                }
            ]
        }

    def deliver_files(self, files: List[str], server_name: str,
                     source_dir: str = None) -> Dict[str, Any]:
        """
        Entrega archivos a un servidor específico.

        Args:
            files: Lista de archivos a entregar
            server_name: Nombre del servidor destino
            source_dir: Directorio fuente (por defecto outputs/reports)

        Returns:
            Dict con resultado de la entrega
        """
        self.logger.info(f"📤 Iniciando entrega de {len(files)} archivos a {server_name}")

        result = {
            "server": server_name,
            "files_requested": len(files),
            "files_delivered": 0,
            "files_failed": 0,
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "errors": []
        }

        # Determinar directorio fuente
        if source_dir is None:
            source_dir = PROJECT_ROOT / "outputs" / "reports"

        # Buscar configuración del servidor
        server_config = None
        for server in self.config.get("servers", []):
            if server["name"] == server_name:
                server_config = server
                break

        if not server_config:
            error_msg = f"Servidor '{server_name}' no encontrado en configuración"
            self.logger.error(f"❌ {error_msg}")
            result["errors"].append(error_msg)
            return result

        if not server_config.get("enabled", False):
            error_msg = f"Servidor '{server_name}' está deshabilitado"
            self.logger.warning(f"⚠️ {error_msg}")
            result["errors"].append(error_msg)
            return result

        # Procesar cada archivo
        for file_path in files:
            try:
                success = self._deliver_single_file(
                    file_path, source_dir, server_config
                )
                if success:
                    result["files_delivered"] += 1
                    self.logger.info(f"✅ Entregado: {file_path}")
                else:
                    result["files_failed"] += 1
                    result["errors"].append(f"Falló entrega de {file_path}")

            except Exception as e:
                result["files_failed"] += 1
                error_msg = f"Error entregando {file_path}: {str(e)}"
                result["errors"].append(error_msg)
                self.logger.error(f"❌ {error_msg}")

        # Determinar éxito general
        result["success"] = result["files_failed"] == 0

        if result["success"]:
            self.logger.info(f"✅ Entrega completada: {result['files_delivered']} archivos entregados")
        else:
            self.logger.error(f"❌ Entrega incompleta: {result['files_delivered']} entregados, {result['files_failed']} fallidos")

        return result

    def _deliver_single_file(self, file_path: str, source_dir: Path,
                           server_config: Dict[str, Any]) -> bool:
        """
        Entrega un archivo individual según configuración del servidor.

        Args:
            file_path: Ruta relativa del archivo
            source_dir: Directorio fuente
            server_config: Configuración del servidor

        Returns:
            True si la entrega fue exitosa
        """
        source_path = source_dir / file_path

        # Verificar que el archivo existe
        if not source_path.exists():
            self.logger.warning(f"⚠️ Archivo no encontrado: {source_path}")
            return False

        server_type = server_config.get("type", "local")
        destination_base = server_config.get("path", "")

        # Resolver variables en la ruta
        destination_base = self._resolve_path_variables(destination_base)

        # Crear ruta de destino completa
        destination_path = Path(destination_base) / file_path

        try:
            # Crear directorio destino si no existe
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Copiar archivo según tipo de servidor
            if server_type == "local":
                return self._deliver_to_local(source_path, destination_path, server_config)

            elif server_type == "network":
                return self._deliver_to_network(source_path, destination_path, server_config)

            elif server_type == "s3":
                return self._deliver_to_s3(source_path, destination_path, server_config)

            elif server_type == "ftp":
                return self._deliver_to_ftp(source_path, destination_path, server_config)

            else:
                self.logger.error(f"❌ Tipo de servidor no soportado: {server_type}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Error en entrega: {e}")
            return False

    def _resolve_path_variables(self, path: str) -> str:
        """
        Resuelve variables en las rutas de destino.

        Args:
            path: Ruta con variables

        Returns:
            Ruta con variables resueltas
        """
        from dotenv import load_dotenv
        load_dotenv()
        desktop_path = os.getenv("DESKTOP_PATH")
        if desktop_path:
            path = path.replace("{DESKTOP_PATH}", desktop_path)

        import getpass

        # Obtener nombre de usuario actual
        username = getpass.getuser()

        # Fecha actual
        today = datetime.now()
        date_vars = {
            "{username}": username,
            "{date}": today.strftime("%Y-%m-%d"),
            "{year}": today.strftime("%Y"),
            "{month}": today.strftime("%m"),
            "{day}": today.strftime("%d")
        }

        for var, value in date_vars.items():
            path = path.replace(var, value)

        print(f"[DEBUG] Resolved delivery path: {path}")
        return path

    def _deliver_to_local(self, source: Path, destination: Path,
                         config: Dict[str, Any]) -> bool:
        """
        Entrega a destino local.
        """
        try:
            overwrite = config.get("overwrite", True)

            if destination.exists() and not overwrite:
                self.logger.info(f"⚠️ Archivo ya existe, omitiendo: {destination}")
                return True

            shutil.copy2(source, destination)
            self.logger.debug(f"📋 Copiado local: {source} → {destination}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error en copia local: {e}")
            return False

    def _deliver_to_network(self, source: Path, destination: Path,
                           config: Dict[str, Any]) -> bool:
        """
        Entrega a servidor en red (SMB/Windows share).
        """
        try:
            # Para Windows shares, usar shutil.copy2 directamente
            # En un entorno real, aquí irían credenciales de red
            shutil.copy2(source, destination)
            self.logger.debug(f"📋 Copiado a red: {source} → {destination}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error en copia de red: {e}")
            return False

    def _deliver_to_s3(self, source: Path, destination: Path,
                       config: Dict[str, Any]) -> bool:
        """
        Entrega a Amazon S3.
        """
        try:
            # TODO: Implementar subida a S3
            # import boto3
            # s3_client = boto3.client('s3')
            # s3_client.upload_file(str(source), config['bucket'], str(destination))

            self.logger.warning("⚠️ Entrega S3 no implementada aún")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error en entrega S3: {e}")
            return False

    def _deliver_dual(self, files: List[str], source_dir: Path,
                     primary_config: Dict[str, Any], secondary_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entrega archivos a dos destinos (dual delivery).
        """
        self.logger.info("🔄 Iniciando entrega dual...")

        result = {
            "primary": {"success": False, "files": [], "errors": []},
            "secondary": {"success": False, "files": [], "errors": []},
            "overall_success": False
        }

        try:
            # 1. Entrega primaria (siempre debe funcionar)
            primary_result = self._deliver_to_primary(files, source_dir, primary_config)
            result["primary"] = primary_result

            if primary_result["success"]:
                self.logger.info(f"✅ Entrega primaria exitosa: {len(primary_result['files'])} archivos")

                # 2. Entrega secundaria (con fallback)
                if self._is_secondary_available(secondary_config):
                    secondary_result = self._deliver_to_secondary(files, source_dir, secondary_config)
                    result["secondary"] = secondary_result

                    if secondary_result["success"]:
                        self.logger.info(f"✅ Entrega secundaria exitosa: {len(secondary_result['files'])} archivos")
                        result["overall_success"] = True
                    else:
                        self.logger.warning(f"⚠️ Entrega secundaria fallida: {secondary_result['errors']}")
                        result["overall_success"] = True  # Primaria exitosa es suficiente
                else:
                    self.logger.warning("⚠️ Destino secundario no disponible - omitiendo")
                    result["secondary"]["errors"].append("Destino secundario no disponible")
                    result["overall_success"] = True  # Primaria exitosa es suficiente
            else:
                self.logger.error(f"❌ Entrega primaria fallida: {primary_result['errors']}")
                result["overall_success"] = False

        except Exception as e:
            self.logger.error(f"❌ Error en entrega dual: {e}")
            result["overall_success"] = False

        return result

    def _deliver_to_primary(self, files: List[str], source_dir: Path,
                           config: Dict[str, Any]) -> Dict[str, Any]:
        """Entrega archivos al destino primario."""
        result = {"success": True, "files": [], "errors": []}

        for file_path in files:
            try:
                src = source_dir / file_path
                dst = source_dir / file_path  # Los archivos ya están en el destino primario

                if src.exists():
                    result["files"].append(file_path)
                    self.logger.debug(f"✅ Archivo primario listo: {file_path}")
                else:
                    result["errors"].append(f"Archivo no encontrado: {file_path}")
                    result["success"] = False

            except Exception as e:
                result["errors"].append(f"Error con {file_path}: {str(e)}")
                result["success"] = False

        return result

    def _deliver_to_secondary(self, files: List[str], source_dir: Path,
                             config: Dict[str, Any]) -> Dict[str, Any]:
        """Entrega archivos al destino secundario."""
        result = {"success": True, "files": [], "errors": []}

        try:
            secondary_path = Path(config.get("path", ""))

            for file_path in files:
                try:
                    src = source_dir / file_path
                    dst = secondary_path / file_path

                    if src.exists():
                        # Crear directorio si no existe
                        dst.parent.mkdir(parents=True, exist_ok=True)

                        # Copiar con sobreescritura
                        import shutil
                        shutil.copy2(src, dst)
                        result["files"].append(file_path)
                        self.logger.debug(f"✅ Copiado a secundario: {file_path}")
                    else:
                        result["errors"].append(f"Archivo fuente no encontrado: {file_path}")
                        result["success"] = False

                except Exception as e:
                    result["errors"].append(f"Error copiando {file_path}: {str(e)}")
                    result["success"] = False

        except Exception as e:
            result["errors"].append(f"Error general en entrega secundaria: {str(e)}")
            result["success"] = False

        return result

    def _is_secondary_available(self, config: Dict[str, Any]) -> bool:
        """Verifica si el destino secundario está disponible."""
        try:
            secondary_path = Path(config.get("path", ""))

            # Verificar si el directorio existe y es escribible
            if secondary_path.exists():
                # Intentar crear un archivo de prueba
                test_file = secondary_path / ".delivery_test"
                test_file.write_text("test")
                test_file.unlink()
                return True
            else:
                self.logger.warning(f"Directorio secundario no existe: {secondary_path}")
                return False

        except Exception as e:
            self.logger.warning(f"Destino secundario no disponible: {e}")
            return False

    def _deliver_to_ftp(self, source: Path, destination: Path,
                       config: Dict[str, Any]) -> bool:
        """
        Entrega via FTP/SFTP.
        """
        try:
            # TODO: Implementar entrega FTP
            # from ftplib import FTP
            # ftp = FTP(config['host'])
            # ftp.login(config['user'], config['password'])

            self.logger.warning("⚠️ Entrega FTP no implementada aún")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error en entrega FTP: {e}")
            return False

    def deliver_to_all_enabled_servers(self, files: List[str]) -> Dict[str, Any]:
        """
        Entrega archivos a todos los servidores habilitados.

        Args:
            files: Lista de archivos a entregar

        Returns:
            Dict con resultados de todas las entregas
        """
        self.logger.info("📤 Entregando a todos los servidores habilitados")

        results = {
            "total_servers": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "server_results": [],
            "timestamp": datetime.now().isoformat()
        }

        enabled_servers = [
            server for server in self.config.get("servers", [])
            if server.get("enabled", False)
        ]

        results["total_servers"] = len(enabled_servers)

        for server in enabled_servers:
            server_result = self.deliver_files(files, server["name"])
            results["server_results"].append(server_result)

            if server_result["success"]:
                results["successful_deliveries"] += 1
            else:
                results["failed_deliveries"] += 1

        self.logger.info(f"📊 Entregas completadas: {results['successful_deliveries']}/{results['total_servers']} servidores")
        return results

    def get_available_servers(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de servidores disponibles.

        Returns:
            Lista de servidores con su información
        """
        servers = []
        for server in self.config.get("servers", []):
            servers.append({
                "name": server["name"],
                "type": server["type"],
                "description": server.get("description", ""),
                "enabled": server.get("enabled", False),
                "files": server.get("files", [])
            })

        return servers

    def test_server_connection(self, server_name: str) -> Dict[str, Any]:
        """
        Prueba la conexión a un servidor.

        Args:
            server_name: Nombre del servidor a probar

        Returns:
            Dict con resultado de la prueba
        """
        self.logger.info(f"🔍 Probando conexión a servidor: {server_name}")

        result = {
            "server": server_name,
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": None
        }

        # Buscar configuración del servidor
        server_config = None
        for server in self.config.get("servers", []):
            if server["name"] == server_name:
                server_config = server
                break

        if not server_config:
            result["error"] = f"Servidor '{server_name}' no encontrado"
            return result

        try:
            server_type = server_config.get("type", "local")
            test_path = server_config.get("path", "")

            if server_type == "local":
                # Verificar que el directorio existe y es escribible
                test_path = self._resolve_path_variables(test_path)
                test_dir = Path(test_path)

                if test_dir.exists():
                    # Intentar crear un archivo de prueba
                    test_file = test_dir / ".connection_test"
                    try:
                        test_file.write_text("test")
                        test_file.unlink()  # Eliminar archivo de prueba
                        result["success"] = True
                    except Exception as e:
                        result["error"] = f"No se puede escribir: {e}"
                else:
                    result["error"] = f"Directorio no existe: {test_path}"

            else:
                # Para otros tipos, marcar como no implementado por ahora
                result["error"] = f"Prueba no implementada para tipo: {server_type}"

        except Exception as e:
            result["error"] = str(e)

        if result["success"]:
            self.logger.info(f"✅ Conexión exitosa a {server_name}")
        else:
            self.logger.error(f"❌ Error de conexión a {server_name}: {result['error']}")

        return result


# Instancia global para uso directo
file_delivery = FileDelivery()

# Funciones de conveniencia para uso directo
def deliver_files(files, server_name, source_dir=None):
    """Función de conveniencia para entregar archivos."""
    return file_delivery.deliver_files(files, server_name, source_dir)

def deliver_to_all_enabled_servers(files):
    """Función de conveniencia para entregar a todos los servidores."""
    return file_delivery.deliver_to_all_enabled_servers(files)

def get_available_servers():
    """Función de conveniencia para obtener servidores disponibles."""
    return file_delivery.get_available_servers()

def test_server_connection(server_name):
    """Función de conveniencia para probar conexión."""
    return file_delivery.test_server_connection(server_name)


if __name__ == "__main__":
    # Ejemplo de uso directo
    import argparse

    parser = argparse.ArgumentParser(description="Sistema de Entrega de Archivos")
    parser.add_argument("--server", help="Nombre del servidor")
    parser.add_argument("--files", nargs="+", help="Archivos a entregar")
    parser.add_argument("--list-servers", action="store_true", help="Listar servidores disponibles")
    parser.add_argument("--test-connection", help="Probar conexión a servidor")

    args = parser.parse_args()

    if args.list_servers:
        servers = get_available_servers()
        print("🖥️ Servidores disponibles:")
        for server in servers:
            status = "✅" if server["enabled"] else "❌"
            print(f"  {status} {server['name']} ({server['type']}): {server['description']}")

    elif args.test_connection:
        result = test_server_connection(args.test_connection)
        if result["success"]:
            print(f"✅ Conexión exitosa a {args.test_connection}")
        else:
            print(f"❌ Error de conexión: {result['error']}")

    elif args.server and args.files:
        result = deliver_files(args.files, args.server)
        if result["success"]:
            print(f"✅ Entrega exitosa: {result['files_delivered']} archivos")
        else:
            print(f"❌ Entrega fallida: {result['errors']}")

    else:
        parser.print_help()