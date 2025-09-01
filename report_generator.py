import pandas as pd
import logging
import json
from typing import List, Dict

from pydantic import ValidationError

from config import settings
from schemas import ProductoStock

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
                        width = 50
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

def generate_especiales_report(df_consolidado: pd.DataFrame, df_especiales_cat: pd.DataFrame):
    """
    Genera el reporte de códigos especiales usando una tabla de Excel formateada,
    poblando el stock desde el dataframe consolidado e incluyendo columnas de almacenes e históricos.
    """
    try:
        logging.info("Iniciando generación de reporte de especiales con formato de tabla...")

        # 1. Usar la plantilla de códigos especiales proporcionada
        df_plantilla = df_especiales_cat.copy()
        logging.info(f"Usando {len(df_plantilla)} códigos desde la plantilla de especiales proporcionada.")

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
        columnas_finales = ['codigo', 'nombre', 'u_por_caja', 'stock_ayer', 'stock_hace_1_semana', 'motivo'] + warehouse_cols
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

def save_current_stock_as_previous(df_consolidado: pd.DataFrame):
    """
    Guarda el stock actual de productos como el stock 'anterior' para la próxima ejecución.
    Guarda solo el código y el stock referencial (VES_disponible).
    """
    try:
        # Asegurarse de que las columnas necesarias existan
        if 'codigo' not in df_consolidado.columns or 'stock_referencial' not in df_consolidado.columns:
            logging.error("df_consolidado no contiene las columnas 'codigo' o 'stock_referencial'. No se guardará el stock anterior.")
            return

        # Crear un diccionario de codigo -> stock_referencial
        previous_stock_data = df_consolidado.set_index('codigo')['stock_referencial'].to_dict()

        # Guardar el diccionario como un archivo JSON
        with open(settings.PREVIOUS_STOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(previous_stock_data, f, indent=4, ensure_ascii=False)
        logging.info(f"Stock actual guardado como stock anterior en {settings.PREVIOUS_STOCK_FILE}")
    except Exception as e:
        logging.error(f"Error al guardar el stock actual como anterior: {e}")
