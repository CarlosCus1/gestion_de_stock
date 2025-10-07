#!/usr/bin/env python3
"""
Script para verificar el codigo 014323 en todo el proceso
"""
import pandas as pd
import os
import sys

def check_file_for_code(filepath, description):
    """Verifica si un archivo contiene el codigo 014323"""
    print(f"\nVerificando {description}: {filepath}")

    if not os.path.exists(filepath):
        print("Archivo no existe")
        return False

    try:
        df = pd.read_excel(filepath)
        print(f"{len(df)} filas, {len(df.columns)} columnas")

        # Buscar codigo 014323
        mask = df['codigo'].astype(str).str.strip() == '014323'
        result = df[mask]

        if len(result) > 0:
            print("CODIGO 014323 ENCONTRADO")
            print(f"   Codigo: {result['codigo'].iloc[0]}")

            # Mostrar stock_referencial si existe
            if 'stock_referencial' in result.columns:
                stock = result['stock_referencial'].iloc[0]
                print(f"   Stock referencial: {stock}")
                if stock > 0:
                    print("STOCK VALIDO ENCONTRADO")
                else:
                    print("STOCK ES CERO")
            else:
                print("Columna stock_referencial no encontrada")

            # Mostrar columnas VES
            ves_cols = [col for col in df.columns if 'ves' in col.lower()]
            if ves_cols:
                print(f"   Columnas VES encontradas: {ves_cols}")
                for col in ves_cols:
                    if col in result.columns:
                        val = result[col].iloc[0]
                        print(f"   {col}: {val}")

            return True
        else:
            print("CODIGO 014323 NO ENCONTRADO")
            # Mostrar algunos codigos de ejemplo
            if 'codigo' in df.columns:
                sample_codes = df['codigo'].head(5).astype(str).tolist()
                print(f"   Codigos de ejemplo: {sample_codes}")
            return False

    except Exception as e:
        print(f"Error al leer archivo: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("VERIFICACION PASO A PASO DEL CODIGO 014323")
    print("=" * 60)

    # Verificar archivos en orden de procesamiento
    files_to_check = [
        ('procesamiento/data_stock_completo.xlsx', 'Datos procesados principales'),
        ('outputs/reports/reporte_stock_hoy.xlsx', 'Reporte principal de stock'),
        ('outputs/reports/reporte_especiales.xlsx', 'Reporte de especiales'),
    ]

    found_in_any = False

    for filepath, description in files_to_check:
        found = check_file_for_code(filepath, description)
        if found:
            found_in_any = True

    print("\n" + "=" * 60)
    if found_in_any:
        print("CODIGO 014323 ENCONTRADO EN ALGUN ARCHIVO")
    else:
        print("CODIGO 014323 NO ENCONTRADO EN NINGUN ARCHIVO")

        # Verificar si hay datos de fallback
        print("\nVerificando si se usaron datos de fallback...")
        try:
            with open('procesamiento/logs/proceso_20251006.log', 'r', encoding='utf-8') as f:
                content = f.read()
                if 'fallback' in content.lower():
                    print("Sistema uso datos de fallback - posible causa del problema")
                else:
                    print("No se detecto uso de fallback")
        except:
            print("No se pudo verificar logs")

if __name__ == "__main__":
    main()