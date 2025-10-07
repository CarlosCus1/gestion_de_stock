import os
import json
import hashlib

def analyze_historical_snapshots():
    historicos_dir = 'procesamiento/historicos'
    files = [f for f in os.listdir(historicos_dir) if f.startswith('stock_snapshot_') and f.endswith('.json')]
    files.sort()

    print(f'Encontrados {len(files)} archivos de snapshots')
    print()

    # Calcular hashes para detectar duplicados
    hashes = {}
    sizes = {}

    for file in files:
        filepath = os.path.join(historicos_dir, file)
        try:
            size = os.path.getsize(filepath)
            sizes[file] = size

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                hash_val = hashlib.md5(content.encode()).hexdigest()
                hashes[file] = hash_val
        except Exception as e:
            print(f'Error leyendo {file}: {e}')
            continue

    print('=== ANÁLISIS DE TAMAÑOS ===')
    sizes_list = [(f, s) for f, s in sizes.items()]
    sizes_list.sort(key=lambda x: x[1], reverse=True)

    for file, size in sizes_list[:10]:  # Mostrar top 10
        print(f'{file}: {size:,} bytes')

    print()
    print('=== ANÁLISIS DE DUPLICADOS ===')
    hash_groups = {}
    for file, hash_val in hashes.items():
        if hash_val not in hash_groups:
            hash_groups[hash_val] = []
        hash_groups[hash_val].append(file)

    duplicates = {h: files for h, files in hash_groups.items() if len(files) > 1}

    if duplicates:
        print(f'Encontrados {len(duplicates)} grupos de archivos duplicados:')
        for hash_val, files in duplicates.items():
            print(f'  Hash {hash_val[:8]}...: {len(files)} archivos')
            for file in files[:5]:  # Mostrar máximo 5 por grupo
                print(f'    - {file}')
            if len(files) > 5:
                print(f'    ... y {len(files) - 5} más')
    else:
        print('No se encontraron archivos duplicados (todos los hashes son únicos)')

    print()
    print('=== VERIFICACIÓN DE INTEGRIDAD ===')
    # Verificar que los archivos sean JSON válidos
    valid_json = 0
    invalid_json = 0
    json_errors = []

    print(f'Verificando {len(files)} archivos...')
    for file in files:
        filepath = os.path.join(historicos_dir, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
            valid_json += 1
        except json.JSONDecodeError as e:
            json_errors.append(f'{file}: JSON inválido - {e}')
            invalid_json += 1
        except UnicodeDecodeError as e:
            json_errors.append(f'{file}: Error de encoding - {e}')
            invalid_json += 1
        except Exception as e:
            json_errors.append(f'{file}: Error general - {e}')
            invalid_json += 1

    print(f'Archivos JSON válidos: {valid_json}')
    print(f'Archivos JSON inválidos: {invalid_json}')

    if json_errors:
        print('Errores encontrados:')
        for error in json_errors[:10]:  # Mostrar máximo 10 errores
            print(f'  {error}')
        if len(json_errors) > 10:
            print(f'  ... y {len(json_errors) - 10} errores más')

    print()
    print('=== ANÁLISIS DE CONTENIDO ===')
    # Verificar algunos archivos para ver si tienen datos razonables
    sample_files = files[-5:]  # Últimos 5 archivos (más recientes)

    for file in sample_files:
        filepath = os.path.join(historicos_dir, file)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            num_products = len(data)
            sample_keys = list(data.keys())[:3] if data else []
            sample_values = [data[k] for k in sample_keys] if sample_keys else []

            print(f'{file}:')
            print(f'  Productos: {num_products}')
            if sample_keys:
                print(f'  Ejemplos: {sample_keys[0]}={sample_values[0]}, {sample_keys[1]}={sample_values[1]}, {sample_keys[2]}={sample_values[2]}')

            # Verificar si el código 014323 está presente
            if '014323' in data:
                print(f'  Código 014323: {data["014323"]} unidades')
            else:
                print(f'  Código 014323: NO ENCONTRADO')
            print()

        except Exception as e:
            print(f'Error analizando {file}: {e}')

if __name__ == "__main__":
    analyze_historical_snapshots()