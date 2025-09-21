#!/usr/bin/env python3
"""
Configuración de Autenticación Google Drive para Gestion360
===========================================================

Este script configura la autenticación con Google Drive API para:
1. Descargar archivos fuente desde 360_base_inicio
2. Subir archivos procesados a 360_salida
3. Sincronizar con carpeta compartida para Google Cloud

Requisitos previos:
1. Crear proyecto en Google Cloud Console
2. Habilitar Google Drive API
3. Crear credenciales OAuth 2.0
4. Descargar credentials.json

Autor: Carlos Cusihuamán
Fecha: 2025-01-20
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

def setup_drive_auth():
    """Configura autenticación con Google Drive"""

    print("🔐 Configuración de Autenticación Google Drive")
    print("=" * 50)

    # Verificar si ya existe token
    if os.path.exists('token.pickle'):
        print("✅ Token de autenticación encontrado")
        print("🔄 Verificando validez...")

        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

        if creds and creds.valid:
            print("✅ Token válido - Autenticación ya configurada")
            print("🎉 Puedes usar los scripts de Drive")
            return True
        elif creds and creds.expired and creds.refresh_token:
            print("🔄 Token expirado, renovando...")
            creds.refresh(Request())

            # Guardar token renovado
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

            print("✅ Token renovado exitosamente")
            return True

    # Verificar si existe credentials.json
    if not os.path.exists('credentials.json'):
        print("❌ No se encontró credentials.json")
        print("\n📋 Pasos para obtener credentials.json:")
        print("1. Ve a: https://console.developers.google.com/")
        print("2. Crea un proyecto o selecciona uno existente")
        print("3. Ve a 'APIs y servicios' > 'Biblioteca'")
        print("4. Busca y habilita 'Google Drive API'")
        print("5. Ve a 'Credenciales' > 'Crear credenciales' > 'ID de cliente OAuth'")
        print("6. Configura:")
        print("   - Tipo de aplicación: 'Aplicación de escritorio'")
        print("   - Nombre: 'Gestion360 Local Processor'")
        print("7. Descarga el archivo JSON como 'credentials.json'")
        print("8. Coloca el archivo en la raíz del proyecto")
        print("\n🔄 Vuelve a ejecutar este script después")
        return False

    print("📄 Encontrado credentials.json")
    print("🌐 Iniciando flujo de autenticación OAuth...")

    try:
        # Configurar scopes para Google Drive
        SCOPES = [
            'https://www.googleapis.com/auth/drive.file',  # Acceso a archivos creados por la app
            'https://www.googleapis.com/auth/drive.readonly'  # Lectura de archivos
        ]

        # Crear flujo de autenticación
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json',
            SCOPES,
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Para aplicaciones de escritorio
        )

        # Ejecutar autenticación
        creds = flow.run_local_server(port=8080)

        # Guardar credenciales
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

        print("\n✅ Autenticación completada exitosamente!")
        print("📁 Token guardado en: token.pickle")
        print("🎉 Ya puedes usar los scripts de Google Drive")

        # Verificar permisos
        print("\n🔍 Verificando permisos...")
        if 'https://www.googleapis.com/auth/drive.file' in creds.scopes:
            print("✅ Permiso para crear/modificar archivos")
        if 'https://www.googleapis.com/auth/drive.readonly' in creds.scopes:
            print("✅ Permiso para leer archivos")

        return True

    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        print("\n💡 Posibles soluciones:")
        print("1. Verifica que credentials.json sea válido")
        print("2. Asegúrate de que Google Drive API esté habilitado")
        print("3. Verifica tu conexión a internet")
        print("4. Intenta cerrar y volver a abrir tu navegador")
        return False

def test_drive_connection():
    """Prueba la conexión con Google Drive"""
    print("\n🧪 Probando conexión con Google Drive...")

    try:
        from googleapiclient.discovery import build

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
            pageSize=5,
            fields="files(name, modifiedTime)"
        ).execute()

        files = results.get('files', [])
        if files:
            print("📁 Archivos recientes en Drive:")
            for file in files:
                print(f"   • {file['name']} ({file['modifiedTime'][:10]})")
        else:
            print("📁 No se encontraron archivos recientes")

        return True

    except Exception as e:
        print(f"❌ Error probando conexión: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Configuración Google Drive para Gestion360")
    print("Este script te ayudará a configurar la autenticación con Google Drive")
    print("para sincronizar archivos entre tu PC y Google Cloud.")
    print()

    # Configurar autenticación
    success = setup_drive_auth()

    if success:
        # Probar conexión
        test_drive_connection()

        print("\n🎯 Próximos pasos:")
        print("1. Coloca tus archivos fuente en: G:\\My Drive\\360_base_inicio\\")
        print("2. Ejecuta: python scripts/drive_centric_processor.py")
        print("3. Los resultados aparecerán en: G:\\My Drive\\360_salida\\")
        print("4. Los archivos se sincronizarán automáticamente con Google Cloud")

        print("\n📋 Archivos esperados en 360_base_inicio:")
        print("   • STOCK_MODELO_COLOR.xls")
        print("   • feriados.xlsx")
        print("   • base_total.xls")
        print("   • codigos_generales.xlsx")

    else:
        print("\n❌ Configuración incompleta")
        print("Sigue las instrucciones anteriores y vuelve a ejecutar este script")

if __name__ == "__main__":
    main()