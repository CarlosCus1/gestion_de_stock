#!/usr/bin/env python3
"""
Script de Prueba para Configuración de Gestion360
===============================================

Este script verifica que todos los componentes estén correctamente
configurados antes de ejecutar el procesamiento completo.

Verificaciones:
- ✅ Dependencias de Python instaladas
- ✅ Autenticación de Google Drive configurada
- ✅ Archivos de entrada accesibles
- ✅ Directorios de salida creados
- ✅ Conexión a Google Drive funcional

Autor: Carlos Cusihuamán
Fecha: 2025-01-20
"""

import os
import sys
import importlib
from pathlib import Path

def print_header(text):
    """Imprimir encabezado formateado"""
    print(f"\n{'='*60}")
    print(f"🔍 {text}")
    print('='*60)

def check_python_version():
    """Verificar versión de Python"""
    print_header("Verificando Versión de Python")

    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 8:
        print("✅ Versión compatible")
        return True
    else:
        print("❌ Se requiere Python 3.8 o superior")
        return False

def check_dependencies():
    """Verificar dependencias instaladas"""
    print_header("Verificando Dependencias")

    required_packages = [
        'pandas',
        'openpyxl',
        'googleapiclient',
        'google.auth',
        'google.cloud.storage',
        'google.cloud.firestore'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            importlib.import_module(package.replace('.', '_') if '.' in package else package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Faltan {len(missing_packages)} paquetes")
        print("Instala con: pip install -r requirements.txt")
        return False

    print("\n✅ Todas las dependencias instaladas")
    return True

def check_drive_auth():
    """Verificar autenticación de Google Drive"""
    print_header("Verificando Autenticación de Google Drive")

    # Verificar credentials.json
    if not os.path.exists('credentials.json'):
        print("❌ No se encontró credentials.json")
        print("📋 Descarga desde Google Cloud Console > APIs y servicios > Credenciales")
        return False

    print("✅ credentials.json encontrado")

    # Verificar token.pickle
    if not os.path.exists('token.pickle'):
        print("⚠️  No se encontró token.pickle")
        print("🔄 Ejecuta: python scripts/setup_drive_auth.py")
        return False

    print("✅ token.pickle encontrado")

    # Intentar importar y verificar
    try:
        from google.oauth2.credentials import Credentials
        import pickle

        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

        if creds and creds.valid:
            print("✅ Token válido")
            return True
        elif creds and creds.expired and creds.refresh_token:
            print("🔄 Token expirado, se renovará automáticamente")
            return True
        else:
            print("❌ Token inválido")
            return False

    except Exception as e:
        print(f"❌ Error verificando token: {e}")
        return False

def check_drive_folders():
    """Verificar carpetas de Google Drive"""
    print_header("Verificando Carpetas de Google Drive")

    drive_paths = [
        r"G:\My Drive\360_base_inicio",
        r"G:\My Drive\360_salida"
    ]

    for path in drive_paths:
        if os.path.exists(path):
            print(f"✅ {path}")

            # Contar archivos
            try:
                files = list(Path(path).glob('*'))
                print(f"   📁 {len(files)} archivos encontrados")
            except:
                print("   ⚠️  Error accediendo a archivos")
        else:
            print(f"❌ {path} no encontrado")
            print("   💡 Crea la carpeta en Google Drive")
    return True  # No bloqueante

def check_local_directories():
    """Verificar directorios locales"""
    print_header("Verificando Directorios Locales")

    directories = [
        'data_sources/raw_reports',
        'data_sources/catalogs',
        'data_sources/base_data',
        'outputs/reports',
        'outputs/json_exports',
        'scripts',
        'logs'
    ]

    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ {directory}")
        else:
            print(f"⚠️  {directory} no existe")
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"   📁 Creado: {directory}")
            except Exception as e:
                print(f"   ❌ Error creando {directory}: {e}")

    return True

def check_input_files():
    """Verificar archivos de entrada"""
    print_header("Verificando Archivos de Entrada")

    input_files = [
        r"G:\My Drive\360_base_inicio\STOCK_MODELO_COLOR.xls",
        r"G:\My Drive\360_base_inicio\feriados.xlsx",
        r"G:\My Drive\360_base_inicio\base_total.xls",
        r"G:\My Drive\360_base_inicio\codigos_generales.xlsx"
    ]

    found_files = 0

    for file_path in input_files:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {os.path.basename(file_path)} ({file_size} bytes)")
            found_files += 1
        else:
            print(f"❌ {os.path.basename(file_path)} no encontrado")

    if found_files == 0:
        print("\n⚠️  No se encontraron archivos de entrada")
        print("💡 Coloca los archivos en G:\\My Drive\\360_base_inicio\\")
        return False

    print(f"\n✅ {found_files}/{len(input_files)} archivos de entrada encontrados")
    return True

def test_drive_connection():
    """Probar conexión con Google Drive"""
    print_header("Probando Conexión con Google Drive")

    try:
        from googleapiclient.discovery import build
        import pickle

        # Cargar credenciales
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

        # Crear servicio
        service = build('drive', 'v3', credentials=creds)

        # Obtener información del usuario
        about = service.about().get(fields="user").execute()
        user_email = about['user']['emailAddress']

        print(f"✅ Conexión exitosa - Usuario: {user_email}")

        # Listar archivos recientes
        results = service.files().list(
            pageSize=3,
            fields="files(name, modifiedTime)"
        ).execute()

        files = results.get('files', [])
        if files:
            print("📁 Archivos recientes en Drive:")
            for file in files[:3]:
                print(f"   • {file['name']} ({file['modifiedTime'][:10]})")

        return True

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Verifica tu conexión a internet y credenciales")
        return False

def main():
    """Función principal de pruebas"""
    print("🧪 Pruebas de Configuración - Gestion360")
    print("Este script verifica que todo esté listo para el procesamiento")
    print()

    tests = [
        ("Versión de Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Autenticación Drive", check_drive_auth),
        ("Directorios locales", check_local_directories),
        ("Carpetas Drive", check_drive_folders),
        ("Archivos de entrada", check_input_files),
        ("Conexión Drive", test_drive_connection)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))

    # Resumen final
    print_header("RESUMEN DE PRUEBAS")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\n📊 Resultado: {passed}/{total} pruebas pasaron")

    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron!")
        print("🚀 Listo para ejecutar: python scripts/drive_centric_processor.py")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron")
        print("💡 Revisa los errores arriba y configura lo necesario")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)