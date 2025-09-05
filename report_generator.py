
import pandas as pd
import logging
import glob
import os
import json
from datetime import datetime
from typing import List, Dict
from pydantic import ValidationError

from config import settings
from schemas import ProductoStock


def generate_historical_general_stock_report(df_generales_cat: pd.DataFrame, df_base: pd.DataFrame):
    """
    Genera un reporte Excel con el histórico de stock VES (stock_referencial)
    para los códigos generales, incluyendo una columna de tendencia.
    """
    logging.info("Generando reporte histórico de stock general (VES_disponible)...")
    try:
        historical_data_list = []
        
        # Obtener todos los archivos de snapshot históricos y ordenarlos por fecha
        snapshot_files = sorted(glob.glob(os.path.join(settings.HISTORICOS_DIR, "stock_snapshot_*.json")))

        # Cargar cada snapshot y añadirlo a la lista
        for file_path in snapshot_files:
            try:
                file_date_str = os.path.basename(file_path).replace("stock_snapshot_", "").replace(".json", "")
                snapshot_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for codigo, stock in data.items():
                        historical_data_list.append({
                            'codigo': str(codigo),
                            'date': snapshot_date,
                            'stock_ves': int(stock)
                        })
            except Exception as e:
                logging.warning(f"Error al cargar el snapshot {file_path}: {e}")
                continue

        if not historical_data_list:
            logging.warning("No se encontraron datos históricos para generar el reporte.")
            return

        df_historical = pd.DataFrame(historical_data_list)
        df_historical['codigo'] = df_historical['codigo'].astype(str).str.strip()

        # Filtrar por códigos generales actuales
        codigos_generales = set(df_generales_cat['codigo'].astype(str).str.strip())
        df_historical_filtered = df_historical[df_historical['codigo'].isin(codigos_generales)].copy()

        if df_historical_filtered.empty:
            logging.warning("No hay datos históricos para los códigos generales.")
            return

        # Pivotear la tabla para tener fechas como columnas
        df_pivot = df_historical_filtered.pivot_table(
            index='codigo',
            columns='date',
            values='stock_ves',
            fill_value=0 # Rellenar con 0 si no hay stock para una fecha
        ).reset_index()

        # Renombrar columnas de fecha a formato YYYY-MM-DD
        df_pivot.columns = [col.strftime('%Y-%m-%d') if isinstance(col, datetime) else col for col in df_pivot.columns]

        # Unir con nombres de productos
        df_product_names = df_base[['codigo', 'nombre']].drop_duplicates(subset=['codigo'])
        df_product_names['codigo'] = df_product_names['codigo'].astype(str).str.strip()
        
        df_reporte = pd.merge(df_pivot, df_product_names, on='codigo', how='left')
        
        # Reordenar columnas: codigo, nombre, luego fechas
        date_cols = sorted([col for col in df_reporte.columns if col not in ['codigo', 'nombre']])
        df_reporte = df_reporte[['codigo', 'nombre'] + date_cols]

        # --- Cálculo de Tendencia ---
        df_reporte['Tendencia'] = ""
        if len(date_cols) >= 7: # Necesitamos al menos 7 días para comparar con hace una semana
            for index, row in df_reporte.iterrows():
                latest_stock = row[date_cols[-1]] # Último día disponible
                stock_7_days_ago = row[date_cols[-7]] if len(date_cols) >= 7 else None # Stock de hace 7 días

                if stock_7_days_ago is not None:
                    if latest_stock > stock_7_days_ago:
                        df_reporte.loc[index, 'Tendencia'] = "📈 Aumento"
                    elif latest_stock < stock_7_days_ago:
                        df_reporte.loc[index, 'Tendencia'] = "📉 Disminución"
                    else:
                        df_reporte.loc[index, 'Tendencia'] = "↔️ Se Mantiene"
                else:
                    df_reporte.loc[index, 'Tendencia'] = "➖ Sin Datos Históricos"
        else:
            df_reporte['Tendencia'] = "➖ Sin Datos Históricos (menos de 7 días)"

        # Guardar en Excel
        output_path = os.path.join(settings.SALIDA_DIR, "reporte_historico_general_VES.xlsx")
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            sheet_name = 'Historico VES'
            df_reporte.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)

            workbook = writer.book
            worksheet = writer.sheets[sheet_name]

            # Configurar cabeceras de tabla
            column_settings = []
            # Formato para centrar el texto
            center_format = workbook.add_format({'align': 'center'})
            for header_name in df_reporte.columns:
                width = max(df_reporte[header_name].astype(str).map(len).max(), len(header_name)) + 2
                cell_format = None
                if header_name == 'nombre':
                    width = 50
                elif header_name == 'Tendencia':
                    width = 20
                    cell_format = center_format # Aplicar formato centrado
                column_settings.append({'header': header_name})
                col_idx = df_reporte.columns.get_loc(header_name)
                worksheet.set_column(col_idx, col_idx, width, cell_format)

            # Añadir la tabla
            (max_row, max_col) = df_reporte.shape
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': column_settings,
                'style': 'Table Style Medium 9',
                'name': 'HistoricoVESReporte'
            })

        logging.info(f"Reporte histórico de stock general (VES_disponible) generado en {output_path}")

    except Exception as e:
        logging.error(f"Error generando reporte_historico_general_VES.xlsx: {e}")

def generate_stock_report(df_base_generales: pd.DataFrame, lineas_a_procesar: List[str]):
    """Genera el reporte de stock general en formato de tabla de Excel con estilos rotativos."""
    try:
        logging.info(f"Total de productos generales en df_base_generales: {len(df_base_generales)}")
        logging.info(f"Líneas únicas en df_base_generales: {df_base_generales['linea'].unique()}")
        with pd.ExcelWriter(settings.OUTPUT_FINAL_REPORT_EXCEL, engine='xlsxwriter') as writer:
            style_index = 0
            for linea in lineas_a_procesar:
                logging.info(f"Procesando línea: {linea}")
                df_linea = df_base_generales[df_base_generales['linea'] == linea].copy()
                if df_linea.empty:
                    logging.warning(f"No se encontraron productos para la línea '{linea}'.")
                    continue

                df_linea = df_linea.sort_values('orden')
                df_linea.insert(0, 'orden_reporte', range(1, 1 + len(df_linea)))

                columnas_reporte = ['orden_reporte', 'codigo', 'nombre', 'u_por_caja', 'stock_referencial']
                if 'ean' in df_linea.columns:
                    columnas_reporte.insert(2, 'ean')
                df_reporte = df_linea[columnas_reporte].copy()

                column_names = ['Orden', 'Código', 'Nombre', 'U. x Caja', 'Stock VES']
                if 'ean' in columnas_reporte:
                    column_names.insert(2, 'EAN')
                df_reporte.columns = column_names

                sheet_name = linea[:31]
                df_reporte.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)

                workbook = writer.book
                worksheet = writer.sheets[sheet_name]

                column_settings = []
                for header_name in df_reporte.columns:
                    width = max(df_reporte[header_name].astype(str).map(len).max(), len(header_name)) + 2
                    if header_name == 'Nombre':
                        width = 50 # Ancho fijo para la columna nombre
                    column_settings.append({'header': header_name})
                    col_idx = df_reporte.columns.get_loc(header_name)
                    worksheet.set_column(col_idx, col_idx, width)

                (max_row, max_col) = df_reporte.shape
                table_style = settings.TABLE_STYLES[style_index % len(settings.TABLE_STYLES)]
                style_index += 1
                
                worksheet.add_table(0, 0, max_row, max_col - 1, {
                    'columns': column_settings,
                    'style': table_style,
                    'name': f'Reporte_{linea.replace(" ", "_")}'
                })

        logging.info(f"reporte_stock_hoy.xlsx generado con formato de tabla.")
    except Exception as e:
        logging.error(f"Error generando reporte_stock_hoy.xlsx: {e}")

def generate_especiales_report(df_consolidado: pd.DataFrame):
    """
    Genera el reporte de códigos especiales usando una tabla de Excel formateada,
    poblando el stock desde el dataframe consolidado e incluyendo columnas de almacenes e históricos.
    """
    try:
        logging.info("Iniciando generación de reporte de especiales con formato de tabla...")

        # 1. Cargar la plantilla de códigos especiales
        df_plantilla = pd.read_excel(settings.INPUT_ESPECIALES_EXCEL, dtype={'codigo': str})
        df_plantilla['codigo'] = df_plantilla['codigo'].str.strip()
        logging.info(f"Cargados {len(df_plantilla)} códigos desde la plantilla de especiales.")

        # Identificar columnas de almacenes dinámicamente
        warehouse_cols = sorted([col for col in df_consolidado.columns if col.endswith('_disponible')])
        logging.info(f"Columnas de almacén detectadas: {warehouse_cols}")

        # 2. Cruzar la plantilla con el df_consolidado
        cols_to_merge = ['codigo', 'nombre', 'u_por_caja', 'stock_ayer', 'stock_hace_1_semana'] + warehouse_cols
        cols_to_merge_exist = [col for col in cols_to_merge if col in df_consolidado.columns]
        
        df_reporte = pd.merge(
            df_plantilla[['codigo', 'motivo']],
            df_consolidado[cols_to_merge_exist],
            on='codigo',
            how='left'
        )
        
        # Rellenar NaNs en columnas numéricas
        numeric_cols_to_fill = warehouse_cols + ['stock_ayer', 'stock_hace_1_semana', 'u_por_caja']
        for col in numeric_cols_to_fill:
            if col in df_reporte.columns:
                df_reporte[col] = df_reporte[col].fillna(0).astype(int)

        # 3. Seleccionar y ordenar las columnas finales
        # Asegurar que las columnas existan y rellenar NaNs con 0 antes de calcular la diferencia
        if 'stock_ayer' not in df_reporte.columns:
            df_reporte['stock_ayer'] = 0
        if 'VES_disponible' not in df_reporte.columns:
            df_reporte['VES_disponible'] = 0

        df_reporte['stock_ayer'] = df_reporte['stock_ayer'].fillna(0).astype(int)
        df_reporte['VES_disponible'] = df_reporte['VES_disponible'].fillna(0).astype(int)

        # Calcular la diferencia (Hoy - Ayer)
        df_reporte['Diferencia_Hoy_Ayer'] = df_reporte['VES_disponible'] - df_reporte['stock_ayer']
        df_reporte['Diferencia_Hoy_Ayer'] = df_reporte['Diferencia_Hoy_Ayer'].apply(lambda x: 0 if x == 0 else x)

        columnas_finales = ['codigo', 'nombre', 'u_por_caja', 'stock_ayer', 'stock_hace_1_semana', 'motivo'] + warehouse_cols + ['Diferencia_Hoy_Ayer']
        columnas_finales_exist = [col for col in columnas_finales if col in df_reporte.columns]
        df_reporte = df_reporte[columnas_finales_exist]
        logging.info(f"Columnas finales del reporte: {df_reporte.columns.tolist()}")

        # 4. Guardar el nuevo reporte usando una tabla de Excel
        with pd.ExcelWriter(settings.OUTPUT_ESPECIALES_REPORT_EXCEL, engine='xlsxwriter') as writer:
            sheet_name = 'Especiales'
            # Escribir el dataframe sin cabecera, la tabla la creará
            df_reporte.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
            
            workbook  = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Crear una lista de diccionarios para las cabeceras de la tabla
            column_settings = []
            for header_name in df_reporte.columns:
                width = max(df_reporte[header_name].astype(str).map(len).max(), len(header_name)) + 2
                if header_name == 'nombre':
                    width = 50 # Ancho fijo para la columna nombre
                column_settings.append({'header': header_name})
                col_idx = df_reporte.columns.get_loc(header_name)
                worksheet.set_column(col_idx, col_idx, width)

            # Añadir la tabla a la hoja de cálculo
            (max_row, max_col) = df_reporte.shape
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': column_settings,
                'style': 'Table Style Medium 9',
                'name': 'ReporteEspeciales'
            })

        logging.info("reporte_especiales.xlsx generado exitosamente con formato de tabla.")

    except FileNotFoundError as e:
        logging.error(f"Error: No se encontró el archivo necesario. {e}")
    except Exception as e:
        logging.error(f"Error generando reporte_especiales.xlsx con el nuevo enfoque: {e}")


def generate_productos_local_json(df_consolidado: pd.DataFrame, lineas_a_procesar: List[str]):
    """Genera el archivo JSON para la webapp (IndexedDB)."""
    try:
        df_productos_local = df_consolidado[df_consolidado['linea'].isin(lineas_a_procesar)].copy()
        if df_productos_local.empty:
            logging.warning("No hay productos para productos_local.json")
            return

        def generate_keywords(row):
            parts = set(str(row.get('nombre', '')).lower().split())
            parts.add(str(row['codigo']).lower())
            if pd.notna(row.get('ean')): parts.add(str(row['ean']).lower().replace('.0',''))
            if pd.notna(row.get('ean_14')): parts.add(str(row['ean_14']).lower().replace('.0',''))
            return ' '.join(sorted(parts))
        df_productos_local['keywords'] = df_productos_local.apply(generate_keywords, axis=1)

        output_cols = ['codigo', 'nombre', 'u_por_caja', 'stock_referencial', 'linea', 'keywords', 'precio', 'can_kg_um']
        if 'ean' in df_productos_local.columns: output_cols.insert(2, 'ean')
        if 'ean_14' in df_productos_local.columns: output_cols.insert(3, 'ean_14')
        
        df_output = df_productos_local[output_cols].copy()

        if 'ean' in df_output.columns: df_output['ean'] = df_output['ean'].astype(str).str.replace(r'\.0$', '', regex=True)
        if 'ean_14' in df_output.columns: df_output['ean_14'] = df_output['ean_14'].astype(str).str.replace(r'\.0$', '', regex=True)

        productos_dict = df_output.to_dict(orient='records')
        with open(settings.OUTPUT_PRODUCTOS_LOCAL_JSON, 'w', encoding='utf-8') as f:
            json.dump(productos_dict, f, indent=4, ensure_ascii=False)
        logging.info(f"productos_local.json generado con {len(productos_dict)} productos.")
    except Exception as e:
        logging.error(f"Error generando productos_local.json: {e}")

def generate_stock_generales_json(df_base_generales: pd.DataFrame, df_base_especiales: pd.DataFrame, lineas_a_procesar: List[str]):
    """Genera el archivo JSON para Firestore/Dialogflow con validación de esquema."""
    try:
        df_generales_filtered = df_base_generales[df_base_generales['linea'].isin(lineas_a_procesar)]
        df_stock_data = pd.concat([df_generales_filtered, df_base_especiales]).drop_duplicates(subset=['codigo'])
        if df_stock_data.empty:
            logging.warning("No hay datos para stock_generales.json")
            return

        warehouse_ids = sorted(set(col.split('_')[0] for col in df_stock_data.columns if '_disponible' in col or '_stock_total' in col))
        
        stock_list = []
        for _, row in df_stock_data.iterrows():
            entry = {
                'codigo': str(row['codigo']),
                'nombre': str(row['nombre']),
                'linea': str(row['linea']),
                'ean': str(row.get('ean', '')).replace('.0', ''),
                'ean_14': str(row.get('ean_14', '')).replace('.0', ''),
                'precio': float(row.get('precio', 0.0)),
                'can_kg_um': float(row.get('can_kg_um') or 0.0),
                'u_por_caja': int(row.get('u_por_caja', 1)),
                'stock_referencial': int(row.get('stock_referencial', 0)),
                'almacenes': {}
            }
            for wh in warehouse_ids:
                entry['almacenes'][wh] = {
                    'total': int(row.get(f"{wh}_stock_total", 0)),
                    'disponible': int(row.get(f"{wh}_disponible", 0))
                }
            stock_list.append(entry)

        # --- PASO DE VALIDACIÓN CON PYDANTIC ---
        validated_stock_list = []
        logging.info(f"Iniciando validación de esquema para {len(stock_list)} productos...")
        for item in stock_list:
            try:
                validated_item = ProductoStock.model_validate(item)
                validated_stock_list.append(validated_item.model_dump())
            except ValidationError as e:
                logging.error(f"Error de validación Pydantic para el producto {item.get('codigo', 'N/A')}: {e}")
                logging.error("La validación del esquema falló. No se generará stock_generales.json para prevenir datos corruptos.")
                return  # Detener la generación de este archivo

        logging.info("Validación de esquema completada con éxito.")
        # --- FIN PASO DE VALIDACIÓN ---

        with open(settings.STOCK_GENERALES_FILE, 'w', encoding='utf-8') as f:
            json.dump(validated_stock_list, f, indent=4, ensure_ascii=False)
        logging.info(f"stock_generales.json generado con {len(validated_stock_list)} productos.")

    except Exception as e:
        logging.error(f"Error generando stock_generales.json: {e}")

def save_daily_stock_snapshot(df_consolidado: pd.DataFrame):
    """
    Guarda un snapshot diario del stock consolidado en un archivo JSON.
    Solo se guarda si no existe un snapshot para el día actual.
    """
    logging.info("Guardando snapshot diario del stock...")
    try:
        snapshot_date = datetime.now().strftime('%Y-%m-%d')
        output_path = os.path.join(settings.HISTORICOS_DIR, f"stock_snapshot_{snapshot_date}.json")
        
        # Verificar si el archivo de snapshot para hoy ya existe
        if os.path.exists(output_path):
            logging.info(f"Snapshot para hoy ({snapshot_date}) ya existe. No se generará uno nuevo.")
            return

        # Seleccionar solo las columnas 'codigo' y 'stock_referencial'
        df_snapshot = df_consolidado[['codigo', 'stock_referencial']].copy()
        
        # Convertir a diccionario para guardar como JSON
        snapshot_data = df_snapshot.set_index('codigo')['stock_referencial'].to_dict()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=4, ensure_ascii=False)
        
        logging.info(f"Snapshot diario guardado en {output_path}")
        
    except Exception as e:
        logging.error(f"Error al guardar el snapshot diario del stock: {e}")
