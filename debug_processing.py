#!/usr/bin/env python3
"""
Script para debuggear el procesamiento del código 014323
"""
import pandas as pd
import os
import sys

def test_api_download():
    """Probar descarga directa de API"""
    print("Probando descarga directa de API...")

    try:
        from data_loader import resilient_downloader
        result = resilient_downloader.download_and_parse_rept_stock()

        if result is not None:
            print(f"Datos obtenidos: {len(result)} productos")

            # Buscar código 014323
            code_14323 = result[result['codigo'] == '014323']
            if len(code_14323) > 0:
                print("CODIGO 014323 encontrado en descarga fresca:")
                print(f"  Codigo: {code_14323['codigo'].iloc[0]}")
                print(f"  Stock referencial: {code_14323['stock_referencial'].iloc[0]}")

                # Mostrar todas las columnas disponibles
                print("Columnas disponibles:")
                for col in sorted(result.columns):
                    if col in code_14323.columns:
                        val = code_14323[col].iloc[0]
                        if 'disponible' in col.lower() or 'stock' in col.lower():
                            print(f"  {col}: {val}")
            else:
                print("CODIGO 014323 NO encontrado en descarga fresca")
                print("Primeros 10 codigos:")
                print(result['codigo'].head(10).tolist())
        else:
            print("Fallo descarga")

    except Exception as e:
        print(f"Error en descarga: {e}")
        import traceback
        traceback.print_exc()

def check_raw_data_processing():
    """Verificar procesamiento de datos crudos"""
    print("\nVerificando procesamiento de datos crudos...")

    try:
        from data_loader import ResilientAPIDownloader
        downloader = ResilientAPIDownloader()

        # Simular descarga para obtener datos crudos
        import requests
        from config import settings

        print("Descargando datos crudos...")
        response = requests.get(settings.STOCK_API_URL, timeout=30)

        if response.status_code == 200:
            print(f"Respuesta obtenida: {len(response.content)} bytes")

            # Procesar como lo hace el sistema
            from io import BytesIO
            df_raw = pd.read_excel(BytesIO(response.content), skiprows=10, dtype=str)
            print(f"Datos crudos: {len(df_raw)} filas, {len(df_raw.columns)} columnas")

            # Buscar TODAS las filas del código en datos crudos
            print("Buscando TODAS las filas de 014323 en datos crudos...")
            found_rows = []
            for idx, row in df_raw.iterrows():
                if str(row.iloc[1]).strip() == '014323':  # Columna 1 es ARTÍCULO
                    almacen = str(row.iloc[9]).strip() if len(row) > 9 else "N/A"
                    disponible = str(row.iloc[18]).strip() if len(row) > 18 else "N/A"
                    found_rows.append({
                        'fila': idx,
                        'almacen': almacen,
                        'disponible': disponible,
                        'stock_total': str(row.iloc[13]).strip() if len(row) > 13 else "N/A",
                        'predespacho': str(row.iloc[16]).strip() if len(row) > 16 else "N/A"
                    })

            if found_rows:
                print(f"ENCONTRADAS {len(found_rows)} filas para 014323:")
                for row_data in found_rows:
                    print(f"  Fila {row_data['fila']}: ALMACEN={row_data['almacen']}, DISPONIBLE={row_data['disponible']}, STOCK_TOTAL={row_data['stock_total']}")
            else:
                print("014323 NO encontrado en datos crudos")
                print("Buscando cualquier fila que contenga '14323'...")
                for idx, row in df_raw.iterrows():
                    articulo = str(row.iloc[1]).strip() if len(row) > 1 else ""
                    if '14323' in articulo:
                        almacen = str(row.iloc[9]).strip() if len(row) > 9 else "N/A"
                        disponible = str(row.iloc[18]).strip() if len(row) > 18 else "N/A"
                        print(f"  Fila {idx}: ARTICULO={articulo}, ALMACEN={almacen}, DISPONIBLE={disponible}")
                        break

        else:
            print(f"Error HTTP: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("DEBUG: Procesamiento del codigo 014323")
    print("=" * 50)

    test_api_download()
    check_raw_data_processing()

if __name__ == "__main__":
    main()