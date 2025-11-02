#!/usr/bin/env python3
"""
Script para generar stock_color.xlsx y colores_por_codigo.json desde STOCK_MODELO_COLOR.xls
Procesa el archivo HTML de stock por colores y genera los archivos correspondientes.
INTEGRACIÓN COMPLETA: Desktop + Parser Apóstrofe + Filtrado + Lógica Inteligente

Funcionalidades:
- Detección automática de archivo en Desktop
- Lógica de "procesar una vez y eliminar"
- Parser de apóstrofe integrado
- Filtrado por códigos válidos
- Verificación inteligente de timestamps
"""

import pandas as pd
import json
import os
import re
import logging
import sys
import shutil
from datetime import datetime, date
from pathlib import Path
from bs4 import BeautifulSoup

# Agregar el directorio raíz al path para importar módulos
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Importar configuración centralizada
try:
    from config import settings
except ImportError:
    # Fallback: intentar importar directamente
    import importlib.util
    config_path = os.path.join(project_root, 'config', 'config.py')
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    settings = config_module.settings

# Configurar logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def setup_logging():
    """Configura el sistema de logging."""
    return logger

def format_codigo_apostrophe(codigo):
    """
    Formatea el código removiendo el apóstrofe SIN agregar ceros extra
    (Integrado desde extract_stock_apostrophe_filtered.py)
    """
    # Remover apóstrofe si existe
    codigo_limpio = codigo.strip("'")
    
    # Extraer solo números
    numeros = re.findall(r'\d+', codigo_limpio)
    if numeros:
        numero = numeros[0]
        
        # Si empieza con 01, mantener formato original SIN agregar ceros
        if numero.startswith('01'):
            # NO agregar ceros extra, mantener como está
            return numero
    
    return None

def parse_html_apostrophe(html_content):
    """
    Parser que reconoce códigos específicamente por el apóstrofe
    (Integrado desde extract_stock_apostrophe_filtered.py)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='pvtTable')
    
    if not table:
        logger.error("❌ No se encontró tabla con clase 'pvtTable'")
        return []
    
    tbody = table.find('tbody')
    if not tbody:
        logger.error("❌ No se encontró tbody en la tabla")
        return []
        
    rows = tbody.find_all('tr')
    
    data = []
    
    # Estado persistente
    current_codigo = ''
    current_descripcion = ''
    
    for row_idx, row in enumerate(rows):
        cells = row.find_all(['th', 'td'])
        
        # Extraer códigos específicamente por apóstrofe
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            
            # RECONOCIMIENTO POR APOSTROFE: Buscar códigos que empiecen con '
            if cell.name == 'th' and cell_text.startswith("'") and re.match(r"^'\d+", cell_text):
                codigo_formateado = format_codigo_apostrophe(cell_text)
                if codigo_formateado:
                    current_codigo = codigo_formateado
                    
                    # Buscar descripción en celdas siguientes de la misma fila
                    cell_idx = cells.index(cell)
                    for next_cell in cells[cell_idx+1:]:
                        if next_cell.name == 'th' and len(next_cell.get_text(strip=True)) > 10:
                            current_descripcion = next_cell.get_text(strip=True)
                            break
                    
                    logger.debug(f"🔍 Código por apóstrofe: '{cell_text}' -> {current_codigo}")
                    break
        
        # Procesar filas de datos (color y cantidad)
        if len(cells) >= 2:
            # Determinar si es una fila de datos
            color = ''
            cantidad = 0
            
            # Buscar color (celda TH sin rowspan y sin apóstrofe)
            for cell in cells:
                if (cell.name == 'th' and 
                    'rowspan' not in cell.attrs and 
                    not cell.get_text(strip=True).startswith("'") and
                    len(cell.get_text(strip=True)) <= 25):  # Colores suelen ser más cortos
                    color = cell.get_text(strip=True)
                    break
            
            # Buscar cantidad (celda TD)
            for cell in cells:
                if cell.name == 'td':
                    try:
                        cantidad_text = cell.get_text(strip=True)
                        # CORRECCIÓN: Manejar correctamente los decimales .000
                        if '.' in cantidad_text:
                            # Si termina en .000, eliminarlo completamente
                            if cantidad_text.endswith('.000'):
                                cantidad = int(cantidad_text[:-4])  # Quitar '.000'
                            else:
                                # Otros decimales, convertir normalmente
                                cantidad = int(float(cantidad_text))
                        else:
                            cantidad = int(cantidad_text)
                        break
                    except:
                        cantidad = 0
                        break
            
            # Agregar registro si tenemos todos los datos necesarios
            if (current_codigo and 
                current_descripcion and 
                color and 
                cantidad > 0 and
                current_codigo.startswith('01')):  # Mantener el filtro adicional
                
                row_data = {
                    'codigo': current_codigo,
                    'descripcion': current_descripcion,
                    'color': color,
                    'unidades': int(cantidad)  # Entero sin decimales
                }
                
                data.append(row_data)
    
    logger.info(f"✅ Parser de apóstrofe procesó {len(data)} filas de datos")
    return data

def check_desktop_file_updated():
    """
    Verifica si el archivo del Desktop es más reciente que los archivos generados
    Returns: dict con información del estado
    """
    desktop_file = r"C:\Users\ccusi\Desktop\STOCK_MODELO_COLOR.xls"
    desktop_log = r"C:\Users\ccusi\Desktop\log.txt"
    processed_marker = "logs/desktop_colors_processed.json"
    work_file = "data_sources/raw_reports/STOCK_MODELO_COLOR.xls"
    
    try:
        # Crear directorios necesarios
        os.makedirs(os.path.dirname(processed_marker), exist_ok=True)
        
        # Verificar si existe archivo en Desktop
        if not os.path.exists(desktop_file):
            return {
                "has_file": False,
                "action": "no_file",
                "message": "No hay archivo en Desktop"
            }
        
        # Verificar si ya fue procesado hoy
        if is_file_already_processed_today(desktop_file, processed_marker):
            logger.info("📅 Archivo ya procesado hoy, eliminando archivos del Desktop")
            try:
                if os.path.exists(desktop_file):
                    os.remove(desktop_file)
                    logger.info("🗑️ STOCK_MODELO_COLOR.xls duplicado eliminado del Desktop")
                if os.path.exists(desktop_log):
                    os.remove(desktop_log)
                    logger.info("🗑️ log.txt duplicado eliminado del Desktop")
            except Exception as e:
                logger.warning(f"⚠️ No se pudieron eliminar archivos duplicados del Desktop: {e}")
            
            return {
                "has_file": True,
                "action": "already_processed",
                "message": "Archivo ya procesado hoy, usando resultados anteriores"
            }
        
        # Verificar timestamps si existe archivo de trabajo
        if os.path.exists(work_file):
            desktop_mtime = os.path.getmtime(desktop_file)
            work_mtime = os.path.getmtime(work_file)
            
            if desktop_mtime > work_mtime:
                logger.info("📱 Archivo del Desktop es más reciente, procesando...")
                return {
                    "has_file": True,
                    "action": "process_new",
                    "message": "Archivo nuevo detectado, procesando",
                    "source": "desktop",
                    "desktop_log": desktop_log
                }
            else:
                logger.info("📁 Archivo del Desktop no es más reciente, usando archivo actual")
                return {
                    "has_file": True,
                    "action": "use_existing",
                    "message": "Usando archivo actual (más reciente)",
                    "source": "existing"
                }
        else:
            # No existe archivo de trabajo, usar Desktop
            logger.info("📱 No existe archivo actual, usando Desktop")
            return {
                "has_file": True,
                "action": "process_new",
                "message": "No hay archivo actual, procesando Desktop",
                "source": "desktop",
                "desktop_log": desktop_log
            }
            
    except Exception as e:
        logger.error(f"❌ Error verificando Desktop: {e}")
        return {
            "has_file": False,
            "action": "error",
            "message": f"Error verificando Desktop: {e}"
        }

def is_file_already_processed_today(file_path, marker_file):
    """Verifica si el archivo ya fue procesado hoy"""
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
        logger.warning(f"⚠️ Error verificando estado de procesamiento: {e}")
        return False

def mark_as_processed(file_path, marker_file):
    """Marca el archivo como procesado"""
    os.makedirs(os.path.dirname(marker_file), exist_ok=True)
    
    data = {
        'file_path': file_path,
        'last_processed_date': datetime.now().strftime('%Y-%m-%d'),
        'last_processed_time': datetime.now().strftime('%H:%M:%S'),
        'processed': True,
        'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
    }
    
    try:
        with open(marker_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"📅 Marcado como procesado: {marker_file}")
    except Exception as e:
        logger.warning(f"⚠️ Error marcando como procesado: {e}")

def load_codigos_generales():
    """
    Carga los códigos generales válidos desde codigos_generales.xlsx
    """
    try:
        codigos_file = "data_sources/catalogs/codigos_generales.xlsx"
        if not os.path.exists(codigos_file):
            logger.warning(f"[WARNING] No se encontró {codigos_file}, procesando todos los códigos")
            return set()

        df_codigos = pd.read_excel(codigos_file, header=None)
        # Asignar headers basados en el orden deseado
        df_codigos.columns = ['orden', 'codigo', 'u_por_caja']
        codigos_validos = set()

        # Extraer códigos no vacíos y normalizarlos
        for _, row in df_codigos.iterrows():
            codigo = str(row.get('codigo', '')).strip()
            if codigo and codigo != 'nan' and not pd.isna(row.get('codigo')):
                # Normalizar: quitar comillas, espacios y convertir a string
                codigo_normalizado = codigo.strip("'\" \t\n\r").strip()
                if codigo_normalizado:
                    codigos_validos.add(codigo_normalizado)

        logger.info(f"[SUCCESS] Cargados {len(codigos_validos)} códigos válidos")
        return codigos_validos

    except Exception as e:
        logger.error(f"[ERROR] Error cargando códigos generales: {e}")
        return set()

def read_excel_file(file_path):
    """
    Lee el archivo Excel y extrae los datos.
    """
    try:
        # Intentar leer con diferentes configuraciones
        df = pd.read_excel(file_path, header=None)
        return df
    except Exception as e:
        logger.error(f"[ERROR] Error leyendo archivo Excel: {e}")
        raise

def process_colors_with_desktop():
    """
    Procesamiento completo con lógica inteligente del Desktop
    """
    logger.info("🎨 Iniciando procesamiento de colores con lógica inteligente...")
    
    # PASO 1: Verificar Desktop
    desktop_check = check_desktop_file_updated()
    logger.info(f"📋 Estado Desktop: {desktop_check['message']}")
    
    # PASO 2: Decidir fuente de datos
    input_file = "data_sources/raw_reports/STOCK_MODELO_COLOR.xls"
    
    if desktop_check["action"] == "process_new":
        # Usar archivo del Desktop
        try:
            desktop_file = r"C:\Users\ccusi\Desktop\STOCK_MODELO_COLOR.xls"
            logger.info(f"📱 Copiando archivo del Desktop...")
            shutil.copy2(desktop_file, input_file)
            logger.info(f"✅ Archivo copiado desde Desktop")
        except Exception as e:
            logger.error(f"❌ Error copiando desde Desktop: {e}")
            return False
            
    elif desktop_check["action"] == "already_processed":
        # Ya procesado, usar archivo existente o terminar
        if os.path.exists(input_file):
            logger.info("📁 Usando archivo existente del último procesamiento")
        else:
            logger.error("❌ No hay archivo para procesar")
            return False
            
    elif desktop_check["action"] == "use_existing":
        # Usar archivo actual (más reciente)
        logger.info("📁 Usando archivo actual existente")
        
    else:  # no_file o error
        # Verificar si hay archivo para usar
        if os.path.exists(input_file):
            logger.info("📁 Usando archivo actual disponible")
        else:
            logger.error("❌ No hay archivo fuente disponible")
            return False
    
    # PASO 3: Procesar datos normalmente
    return process_colors_data(input_file, desktop_check)

def process_colors_data(input_file, desktop_check):
    """
    Procesamiento principal de datos de colores
    """
    try:
        # Cargar códigos válidos
        logger.info("[INFO] Cargando códigos generales válidos...")
        codigos_validos = load_codigos_generales()
        
        # Leer archivo HTML
        logger.info("[INFO] Leyendo archivo de datos...")
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parsear con parser de apóstrofe
        logger.info("[INFO] Parseando datos con reconocimiento de apóstrofe...")
        df = parse_html_apostrophe_to_dataframe(html_content)
        
        if df is None or df.empty:
            logger.error("❌ No se pudieron extraer datos")
            return False
        
        # Generar archivos
        success = generate_output_files(df, codigos_validos, desktop_check)
        
        # Marcar como procesado si viene del Desktop
        if desktop_check["action"] == "process_new":
            desktop_file = r"C:\Users\ccusi\Desktop\STOCK_MODELO_COLOR.xls"
            desktop_log = r"C:\Users\ccusi\Desktop\log.txt"
            marker_file = "logs/desktop_colors_processed.json"
            mark_as_processed(desktop_file, marker_file)
            
            # Eliminar archivos del Desktop (limpieza completa)
            try:
                if os.path.exists(desktop_file):
                    os.remove(desktop_file)
                    logger.info("🗑️ STOCK_MODELO_COLOR.xls eliminado del Desktop")
                if os.path.exists(desktop_log):
                    os.remove(desktop_log)
                    logger.info("🗑️ log.txt eliminado del Desktop")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar archivos del Desktop: {e}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error procesando datos: {e}")
        return False

def parse_html_apostrophe_to_dataframe(html_content):
    """
    Convierte el resultado del parser de apóstrofe a DataFrame
    """
    try:
        data = parse_html_apostrophe(html_content)
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        # Aplicar filtros adicionales
        df = df[df['unidades'] > 0]  # Solo unidades positivas
        df = df[df['codigo'].str.len() > 0]  # Códigos no vacíos
        
        logger.info(f"📊 Datos parseados: {len(df)} filas válidas")
        return df
        
    except Exception as e:
        logger.error(f"❌ Error convirtiendo a DataFrame: {e}")
        return None

def generate_output_files(df, codigos_validos, desktop_check):
    """
    Genera los archivos de salida (Excel y JSON)
    """
    try:
        # Crear directorios de salida
        output_dir = "outputs/reports"
        os.makedirs(output_dir, exist_ok=True)
        
        output_xlsx = os.path.join(output_dir, "stock_color.xlsx")
        output_json = os.path.join(output_dir, "colores_por_codigo.json")
        
        # Filtrar por códigos válidos
        if codigos_validos:
            df_filtered = df[df['codigo'].isin(codigos_validos)].copy()
            logger.info(f"🔍 Filtrado: {len(df)} → {len(df_filtered)} códigos válidos")
        else:
            df_filtered = df.copy()
            logger.info("🔍 Sin filtro de códigos válidos")
        
        if df_filtered.empty:
            logger.error("❌ No hay datos después del filtrado")
            return False
        
        # Generar Excel
        logger.info("[INFO] Generando stock_color.xlsx...")
        with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
            df_filtered.to_excel(writer, sheet_name='Colores', index=False)
            
            # Formato básico
            worksheet = writer.sheets['Colores']
            worksheet.set_column(0, 0, 12)  # codigo
            worksheet.set_column(1, 1, 50)  # descripcion
            worksheet.set_column(2, 2, 25)  # color
            worksheet.set_column(3, 3, 10)  # unidades
        
        logger.info(f"✅ stock_color.xlsx generado: {output_xlsx}")
        
        # Generar JSON
        logger.info("[INFO] Generando colores_por_codigo.json...")
        colores_por_codigo = {}
        
        for _, row in df_filtered.iterrows():
            codigo = str(row['codigo']).strip()
            descripcion = str(row['descripcion']).strip()
            color = str(row['color']).strip()
            unidades = int(row['unidades'])
            
            if codigo not in colores_por_codigo:
                colores_por_codigo[codigo] = {
                    'descripcion': descripcion,
                    'colores': []
                }
            
            colores_por_codigo[codigo]['colores'].append({
                'color': color,
                'unidades': unidades
            })
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(colores_por_codigo, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ colores_por_codigo.json generado: {output_json}")
        logger.info(f"📈 Total códigos procesados: {len(colores_por_codigo)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generando archivos: {e}")
        return False

def generate_colores_files():
    """
    Función principal unificada para generar archivos de colores
    """
    logger.info("🎨 Iniciando generación de archivos de colores...")
    
    try:
        # Ejecutar procesamiento con lógica inteligente
        success = process_colors_with_desktop()
        
        if success:
            logger.info("🎉 Proceso completado exitosamente")
            return True
        else:
            logger.error("💥 Proceso falló")
            return False
            
    except Exception as e:
        logger.error(f"💥 Error fatal en generación de colores: {e}")
        return False

if __name__ == "__main__":
    logger = setup_logging()
    logger.info("[INFO] Iniciando generación de archivos de colores con Desktop...")
    success = generate_colores_files()
    if success:
        logger.info("[SUCCESS] Proceso completado exitosamente")
    else:
        logger.error("[ERROR] Proceso falló")
        exit(1)