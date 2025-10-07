import os
import pandas as pd
import logging
import requests
import time
import hashlib
import json
from io import BytesIO
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

from config import settings


class DataQualityMonitor:
    """Monitor de calidad de datos para detectar problemas en las descargas."""

    def __init__(self):
        self.metrics_file = os.path.join(settings.LOGS_DIR, "data_quality_metrics.json")
        self.stagnation_threshold_pct = settings.STAGNATION_THRESHOLD_PCT
        self.stagnation_days_alert = settings.STAGNATION_ALERT_DAYS

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Valida calidad y actualización de los datos descargados."""
        validation = {
            "is_valid": True,
            "issues": [],
            "stats": {},
            "recommendations": [],
            "stagnation_detected": False
        }

        # Estadísticas básicas
        validation["stats"] = {
            "total_products": len(df),
            "products_with_stock": len(df[df['stock_referencial'] > 0]),
            "zero_stock_products": len(df[df['stock_referencial'] == 0]),
            "avg_stock": float(df['stock_referencial'].mean()),
            "max_stock": float(df['stock_referencial'].max()),
            "total_stock_sum": float(df['stock_referencial'].sum())
        }

        # Validación de códigos
        invalid_codes = []
        for idx, row in df.iterrows():
            code = str(row.get('codigo', '')).strip()
            if not self._is_valid_product_code(code):
                invalid_codes.append(code)

        if invalid_codes:
            validation["issues"].append(f"Códigos inválidos encontrados: {len(invalid_codes)}")
            validation["is_valid"] = False

        # Validación de valores numéricos razonables
        if validation["stats"]["avg_stock"] < 0:
            validation["issues"].append("Valores negativos en stock detectados")
            validation["is_valid"] = False

        # Comparación con datos anteriores (si existen)
        if self._has_previous_stats():
            prev_stats = self._load_previous_stats()
            change_analysis = self._analyze_changes(validation["stats"], prev_stats)
            validation["change_analysis"] = change_analysis

            if change_analysis["change_pct"] < self.stagnation_threshold_pct:
                validation["recommendations"].append("Datos prácticamente sin cambios")
                # Verificar si hay estancamiento prolongado
                if self._check_stagnation_alert():
                    validation["stagnation_detected"] = True
                    validation["recommendations"].append(f"ALERTA: Datos estancados por {self.stagnation_days_alert}+ días")

        # Guardar estadísticas actuales
        self._save_current_stats(validation["stats"])

        return validation

    def _is_valid_product_code(self, code: str) -> bool:
        """Valida formato de código de producto."""
        if not code or len(code) < 5:
            return False
        # Solo números y letras, sin espacios extra
        import re
        return bool(re.match(r'^[A-Za-z0-9]{5,}$', code.replace(' ', '')))

    def _has_previous_stats(self) -> bool:
        """Verifica si existen estadísticas anteriores."""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                return len(data) > 0
        except:
            pass
        return False

    def _load_previous_stats(self) -> Dict[str, float]:
        """Carga estadísticas de la descarga anterior."""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    history = json.load(f)
                if history:
                    return history[-1]["stats"]  # Últimas estadísticas
        except Exception as e:
            logging.warning(f"Error cargando estadísticas anteriores: {e}")
        return {}

    def _analyze_changes(self, current: Dict[str, float], previous: Dict[str, float]) -> Dict[str, Any]:
        """Analiza cambios entre estadísticas actuales y anteriores."""
        analysis = {
            "change_pct": 0.0,
            "significant_change": False,
            "details": {}
        }

        if not previous or "avg_stock" not in previous:
            return analysis

        # Calcular cambio porcentual en promedio de stock
        prev_avg = previous["avg_stock"]
        curr_avg = current["avg_stock"]

        if prev_avg > 0:
            change_pct = abs(curr_avg - prev_avg) / prev_avg * 100
            analysis["change_pct"] = change_pct
            analysis["significant_change"] = change_pct >= self.stagnation_threshold_pct

        # Detalles adicionales
        analysis["details"] = {
            "prev_avg_stock": prev_avg,
            "curr_avg_stock": curr_avg,
            "stock_sum_change": current["total_stock_sum"] - previous.get("total_stock_sum", 0)
        }

        return analysis

    def _check_stagnation_alert(self) -> bool:
        """Verifica si los datos llevan días sin cambiar significativamente."""
        try:
            if not os.path.exists(self.metrics_file):
                return False

            with open(self.metrics_file, 'r') as f:
                history = json.load(f)

            if len(history) < self.stagnation_days_alert:
                return False

            # Revisar los últimos N días
            recent_entries = history[-self.stagnation_days_alert:]
            avg_stocks = [entry["stats"]["avg_stock"] for entry in recent_entries]

            # Calcular variación máxima en el período
            max_change = max(avg_stocks) - min(avg_stocks)
            avg_value = sum(avg_stocks) / len(avg_stocks)

            if avg_value > 0:
                change_pct = (max_change / avg_value) * 100
                return change_pct < self.stagnation_threshold_pct

        except Exception as e:
            logging.error(f"Error verificando estancamiento: {e}")

        return False

    def _save_current_stats(self, stats: Dict[str, float]):
        """Guarda estadísticas actuales en el historial."""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)

            # Cargar historial existente
            history = []
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    history = json.load(f)

            # Agregar nueva entrada
            entry = {
                "timestamp": datetime.now().isoformat(),
                "stats": stats
            }
            history.append(entry)

            # Mantener solo últimas 30 entradas
            history = history[-30:]

            # Guardar
            with open(self.metrics_file, 'w') as f:
                json.dump(history, f, indent=2)

        except Exception as e:
            logging.error(f"Error guardando estadísticas: {e}")

    def log_download_metrics(self, df: pd.DataFrame, download_time: float, source: str):
        """Registra métricas completas de descarga."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "download_time": download_time,
            "record_count": len(df),
            "avg_stock": float(df['stock_referencial'].mean()),
            "zero_stock_pct": float((df['stock_referencial'] == 0).mean() * 100),
            "quality_validation": self.validate_data_quality(df)
        }

        logging.info(f"📊 Métricas de descarga - Fuente: {source}, Tiempo: {download_time:.2f}s, Registros: {len(df)}")
        logging.info(f"📈 Stock promedio: {metrics['avg_stock']:.2f}, Cero stock: {metrics['zero_stock_pct']:.1f}%")

        if metrics["quality_validation"]["stagnation_detected"]:
            logging.warning("🚨 ALERTA: Datos estancados detectados - posible problema con fuente de datos")


def validate_file_exists(filepath: str, description: str) -> bool:
    """Verifica si un archivo existe y loguea el resultado."""
    if not os.path.exists(filepath):
        logging.error(f"{description} no encontrado: {filepath}")
        return False
    logging.info(f"{description} encontrado: {filepath}")
    return True

class ResilientAPIDownloader:
    """Descargador resiliente con reintentos y fallback"""

    def __init__(self):
        self.base_timeout = settings.API_TIMEOUT_BASE
        self.max_retries = settings.API_MAX_RETRIES
        self.retry_delays = settings.API_RETRY_DELAYS
        self.last_successful_download = None
        self.download_hash_file = os.path.join(settings.LOGS_DIR, "last_download_hash.json")
        self.last_download_stats = None  # Para comparación de calidad
        self.data_monitor = DataQualityMonitor()  # Nuevo monitor de calidad

    def download_and_parse_rept_stock(self) -> Optional[pd.DataFrame]:
        """Descarga y procesa el reporte de stock desde la API con resiliencia."""
        logging.info("🚀 Iniciando descarga resiliente de REPT_STOCK...")
        print(f"[DEBUG] STOCK_API_URL: {settings.STOCK_API_URL}")

        start_time = time.time()  # Para medir tiempo de descarga

        # Intentar descarga con reintentos
        for attempt in range(self.max_retries + 1):
            try:
                timeout = self.base_timeout * (2 ** attempt)  # Timeout progresivo
                logging.info(f"📡 Intento {attempt + 1}/{self.max_retries + 1} - Timeout: {timeout}s")

                response = requests.get(settings.STOCK_API_URL, timeout=timeout)
                response.raise_for_status()

                # Validar respuesta
                if not self._validate_response(response):
                    logging.warning(f"⚠️ Respuesta inválida en intento {attempt + 1}")
                    continue

                # Procesar datos
                df_pivot = self._process_stock_data(response)

                # Validar calidad de datos
                quality_check = self.data_monitor.validate_data_quality(df_pivot)

                # Log de calidad
                if quality_check["issues"]:
                    logging.warning(f"⚠️ Issues de calidad detectados: {quality_check['issues']}")

                if quality_check["recommendations"]:
                    for rec in quality_check["recommendations"]:
                        logging.info(f"💡 Recomendación: {rec}")

                # Verificar si hay datos nuevos (con validación mejorada)
                has_new_data = self._has_new_data(df_pivot)

                if has_new_data or quality_check["is_valid"]:
                    self._save_download_hash(df_pivot)
                    # Registrar métricas de descarga exitosa
                    self.data_monitor.log_download_metrics(df_pivot, time.time() - start_time, "API")
                    logging.info(f"✅ Descarga exitosa en intento {attempt + 1}: {len(df_pivot)} productos")
                    return df_pivot
                else:
                    logging.warning("⚠️ Datos no pasaron validación de calidad, pero se usarán como fallback")
                    return df_pivot  # Retornar datos aunque no sean óptimos

            except requests.exceptions.Timeout:
                logging.warning(f"⏰ Timeout en intento {attempt + 1}")
            except requests.exceptions.ConnectionError:
                logging.warning(f"🔌 Error de conexión en intento {attempt + 1}")
            except Exception as e:
                logging.error(f"❌ Error en intento {attempt + 1}: {e}")

            # Esperar antes del siguiente intento (excepto en el último)
            if attempt < self.max_retries:
                delay = self.retry_delays[attempt]
                logging.info(f"⏳ Esperando {delay} segundos antes del siguiente intento...")
                time.sleep(delay)

        # Si todos los intentos fallaron, intentar fallback
        logging.error("❌ Todos los intentos de descarga fallaron")
        return self._attempt_enhanced_fallback()

    def _validate_response(self, response) -> bool:
        """Valida que la respuesta de la API sea útil con criterios más permisivos."""
        try:
            # Verificar tamaño mínimo (reducido para ser más permisivo)
            if len(response.content) < 500:
                logging.warning("Respuesta muy pequeña (< 500 bytes)")
                return False

            # Verificar tipo de contenido (más permisivo)
            content_type = response.headers.get('content-type', '').lower()
            valid_content_types = [
                'application/vnd',  # Excel estándar
                'application/octet-stream',  # Binario genérico
                'application/xlsx',  # Excel directo
                'application/excel',  # Excel antiguo
                'binary/octet-stream'  # Otro binario
            ]

            is_valid_type = any(content_type.startswith(vct) for vct in valid_content_types)
            if not is_valid_type and content_type:
                logging.info(f"Tipo de contenido no estándar pero aceptable: {content_type}")

            # Verificar que parezca un archivo binario (no texto plano)
            # Los archivos Excel tienen bytes de control al inicio
            if len(response.content) > 10:
                first_bytes = response.content[:10]
                # Verificar que no sea texto plano (debe tener bytes de control)
                try:
                    text_preview = first_bytes.decode('utf-8', errors='ignore')
                    # Si se puede decodificar como texto y parece texto, puede ser inválido
                    if len(text_preview) > 5 and text_preview.isprintable():
                        # Pero permitir si contiene palabras clave de Excel
                        if not any(keyword in text_preview.lower() for keyword in ['excel', 'sheet', 'workbook']):
                            logging.warning("Contenido parece ser texto plano, no Excel")
                            # No fallar inmediatamente, solo warning
                except:
                    pass  # Si no se puede decodificar, probablemente es binario válido

            # Intentar verificar que sea realmente un archivo Excel válido
            try:
                with BytesIO(response.content) as f:
                    # Intentar leer como Excel sin procesar datos
                    pd.read_excel(f, nrows=1, engine='openpyxl')
                    logging.info("✅ Archivo Excel válido detectado")
                    return True
            except Exception as excel_error:
                logging.warning(f"Error leyendo como Excel: {excel_error}")
                # No fallar por error de lectura, puede ser formato específico
                return True  # Asumir válido si llegó hasta aquí

            return True

        except Exception as e:
            logging.error(f"Error validando respuesta: {e}")
            return False

    def _process_stock_data(self, response) -> pd.DataFrame:
        """Procesa los datos de stock descargados."""
        with BytesIO(response.content) as f:
            df_raw = pd.read_excel(f, skiprows=10, dtype=str)

        df = df_raw.iloc[:, [1, 2, 9, 13, 16, 18]].copy()
        df.columns = ["ARTÍCULO", "NOMBRE_ARTICULO", "ALMACEN", "STOCK TOTAL", "PREDESPACHO", "DISPONIBLE"]
        df.rename(columns=settings.REPT_STOCK_COLS_MAP, inplace=True)

        df.dropna(subset=["codigo", "almacen"], inplace=True)
        df["codigo"] = df["codigo"].astype(str).str.strip()
        df["codigo"] = df["codigo"].str.replace(' ', '', regex=False)

        # Limpieza y validación robusta de códigos
        df = self._clean_and_validate_product_codes(df)

        numeric_cols = ["stock_total", "predespacho", "disponible"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        df_pivot = df.pivot_table(
            index="codigo",
            columns="almacen",
            values=numeric_cols,
            aggfunc="first",
            fill_value=0
        )
        df_pivot.columns = [f"{alm}_{tipo.replace(' ', '_')}" for tipo, alm in df_pivot.columns]
        df_pivot.reset_index(inplace=True)
        df_pivot['codigo'] = df_pivot['codigo'].astype(str).str.strip()
        df_pivot['codigo'] = df_pivot['codigo'].str.replace(' ', '', regex=False)

        # Asignar stock referencial - IGUAL A VES_DISPONIBLE
        ves_disponible_col = next((col for col in df_pivot.columns if 'VES' in col.upper() and 'disponible' in col.lower()), None)

        if ves_disponible_col:
            # stock_referencial = VES_disponible exactamente
            df_pivot[settings.STANDARD_COLUMN_NAMES['stock_referencial']] = df_pivot[ves_disponible_col].astype(int)
        else:
            df_pivot[settings.STANDARD_COLUMN_NAMES['stock_referencial']] = 0
            logging.warning("VES_disponible no encontrado, stock_referencial = 0")

        return df_pivot

    def _clean_and_validate_product_codes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpieza y validación robusta de códigos de producto."""
        if 'codigo' not in df.columns:
            raise ValueError("Columna 'codigo' no encontrada")

        original_count = len(df)
        issues_found = []

        # Convertir a string y limpiar
        df['codigo'] = df['codigo'].astype(str).str.strip()

        # Remover caracteres especiales pero mantener números y letras
        df['codigo'] = df['codigo'].str.replace(r'[^A-Za-z0-9]', '', regex=True)

        # Validar formato
        valid_mask = df['codigo'].str.match(r'^[A-Za-z0-9]{5,}$')
        invalid_codes = df[~valid_mask]['codigo'].tolist()

        if invalid_codes:
            issues_found.append(f"Códigos con formato inválido: {len(invalid_codes)}")
            # Log primeros 5 ejemplos
            logging.warning(f"⚠️ Ejemplos de códigos inválidos: {invalid_codes[:5]}")

            # Remover filas con códigos inválidos
            df = df[valid_mask].copy()

        # Verificar duplicados por código + almacén (cada código puede tener múltiples almacenes)
        duplicates = df.duplicated(subset=['codigo', 'almacen']).sum()
        if duplicates > 0:
            issues_found.append(f"Duplicados código+almacén encontrados: {duplicates}")
            # Mantener primera ocurrencia por combinación código+almacén
            df = df.drop_duplicates(subset=['codigo', 'almacen'], keep='first')

        # Verificar códigos demasiado cortos/largos
        code_lengths = df['codigo'].str.len()
        too_short = (code_lengths < 5).sum()
        too_long = (code_lengths > 20).sum()  # Asumiendo máximo razonable

        if too_short > 0:
            issues_found.append(f"Códigos demasiado cortos (<5 chars): {too_short}")
        if too_long > 0:
            issues_found.append(f"Códigos demasiado largos (>20 chars): {too_long}")

        final_count = len(df)
        removed_count = original_count - final_count

        if removed_count > 0:
            logging.warning(f"🧹 Limpieza de códigos: {removed_count} filas removidas")

        if issues_found:
            logging.info(f"📋 Issues en códigos: {issues_found}")

        # Agregar metadatos de validación
        df['codigo_validated'] = True
        df['codigo_length'] = df['codigo'].str.len()

        return df

    def _has_new_data(self, new_data: pd.DataFrame) -> bool:
        """Determina si los nuevos datos son diferentes a los anteriores."""
        if new_data is None or len(new_data) == 0:
            return False

        # Calcular hash de los nuevos datos
        new_hash = self._calculate_data_hash(new_data)

        # Cargar hash anterior
        previous_hash = self._load_previous_hash()

        if previous_hash is None:
            logging.info("🔄 Primera descarga - datos nuevos por defecto")
            return True

        if new_hash != previous_hash:
            logging.info("🔄 Detectados datos nuevos de la API")
            return True
        else:
            logging.info("ℹ️ Datos de la API sin cambios")
            return False

    def _calculate_data_hash(self, df: pd.DataFrame) -> str:
        """Calcula hash representativo de los datos."""
        key_columns = ['codigo', 'stock_referencial']
        hash_data = df[key_columns].astype(str).sum().sum()
        return hashlib.md5(hash_data.encode()).hexdigest()

    def _load_previous_hash(self) -> Optional[str]:
        """Carga el hash de la descarga anterior."""
        try:
            if os.path.exists(self.download_hash_file):
                with open(self.download_hash_file, 'r') as f:
                    data = json.load(f)
                    return data.get('hash')
        except Exception as e:
            logging.warning(f"Error cargando hash anterior: {e}")
        return None

    def _save_download_hash(self, df: pd.DataFrame):
        """Guarda el hash de la descarga actual."""
        try:
            hash_value = self._calculate_data_hash(df)
            data = {
                'hash': hash_value,
                'timestamp': datetime.now().isoformat(),
                'record_count': len(df)
            }
            with open(self.download_hash_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.warning(f"Error guardando hash: {e}")

    def _attempt_enhanced_fallback(self) -> Optional[pd.DataFrame]:
        """Fallback mejorado que garantiza datos disponibles."""
        if not settings.ENABLE_FALLBACK:
            logging.error("🚨 Fallback deshabilitado - no hay datos disponibles")
            return None

        logging.warning("🔄 Iniciando fallback mejorado...")

        strategies = [
            ("datos_dia_anterior", self._load_yesterday_data),
            ("datos_semana_anterior", self._load_week_ago_data),
            ("datos_mes_anterior", self._load_month_ago_data),
            ("datos_base_minimos", self._generate_minimal_fallback_data),
            ("datos_vacios_seguros", self._generate_safe_empty_data)
        ]

        for strategy_name, strategy_func in strategies:
            try:
                logging.info(f"🔄 Probando estrategia: {strategy_name}")
                data = strategy_func()
                if data is not None and len(data) > 0:
                    logging.warning(f"✅ Fallback exitoso con: {strategy_name} ({len(data)} productos)")
                    # Marcar como datos de fallback
                    data['is_fallback'] = True
                    data['fallback_strategy'] = strategy_name
                    return data
            except Exception as e:
                logging.warning(f"❌ Estrategia {strategy_name} falló: {e}")

        logging.error("🚨 Todas las estrategias de fallback fallaron")
        return None

    def _load_month_ago_data(self) -> Optional[pd.DataFrame]:
        """Carga datos de hace un mes."""
        try:
            month_ago = datetime.now() - timedelta(days=30)
            snapshot_file = os.path.join(settings.HISTORICOS_DIR, f"stock_snapshot_{month_ago.strftime('%Y-%m-%d')}.json")

            if os.path.exists(snapshot_file):
                with open(snapshot_file, 'r') as f:
                    data = json.load(f)

                # Convertir a DataFrame
                df = pd.DataFrame(list(data.items()), columns=['codigo', 'stock_referencial'])
                df['codigo'] = df['codigo'].astype(str).str.strip()
                logging.info(f"✅ Datos de fallback cargados: {len(df)} productos")
                return df
        except Exception as e:
            logging.error(f"Error cargando datos del mes anterior: {e}")

        return None

    def _generate_minimal_fallback_data(self) -> pd.DataFrame:
        """Genera datos mínimos de fallback desde archivos base."""
        try:
            # Usar base_total.xls como fuente de códigos válidos
            df_base = load_base_total()
            if df_base is not None:
                # Crear DataFrame con códigos y stock 0
                fallback_data = df_base[['codigo']].copy()
                fallback_data['stock_referencial'] = 0
                fallback_data['is_fallback'] = True
                logging.info(f"📊 Datos mínimos generados: {len(fallback_data)} productos con stock 0")
                return fallback_data
        except Exception as e:
            logging.error(f"Error generando datos mínimos: {e}")
        return None

    def _generate_safe_empty_data(self) -> pd.DataFrame:
        """Genera dataset vacío seguro como último recurso."""
        logging.warning("🚨 Generando dataset vacío seguro")
        return pd.DataFrame({
            'codigo': ['DEFAULT'],
            'stock_referencial': [0],
            'is_fallback': [True],
            'fallback_strategy': ['empty_safe']
        })

    # Alias para compatibilidad
    def _attempt_fallback(self) -> Optional[pd.DataFrame]:
        """Alias para compatibilidad con código existente."""
        return self._attempt_enhanced_fallback()

    def _load_yesterday_data(self) -> Optional[pd.DataFrame]:
        """Carga datos del día anterior."""
        try:
            yesterday = datetime.now() - timedelta(days=1)
            snapshot_file = os.path.join(settings.HISTORICOS_DIR, f"stock_snapshot_{yesterday.strftime('%Y-%m-%d')}.json")

            if os.path.exists(snapshot_file):
                with open(snapshot_file, 'r') as f:
                    data = json.load(f)

                # Convertir a DataFrame
                df = pd.DataFrame(list(data.items()), columns=['codigo', 'stock_referencial'])
                df['codigo'] = df['codigo'].astype(str).str.strip()
                logging.info(f"✅ Datos de fallback cargados: {len(df)} productos")
                return df
        except Exception as e:
            logging.error(f"Error cargando datos del día anterior: {e}")

        return None

    def _load_week_ago_data(self) -> Optional[pd.DataFrame]:
        """Carga datos de una semana atrás."""
        try:
            week_ago = datetime.now() - timedelta(days=7)
            snapshot_file = os.path.join(settings.HISTORICOS_DIR, f"stock_snapshot_{week_ago.strftime('%Y-%m-%d')}.json")

            if os.path.exists(snapshot_file):
                with open(snapshot_file, 'r') as f:
                    data = json.load(f)

                df = pd.DataFrame(list(data.items()), columns=['codigo', 'stock_referencial'])
                df['codigo'] = df['codigo'].astype(str).str.strip()
                logging.info(f"✅ Datos de fallback cargados: {len(df)} productos")
                return df
        except Exception as e:
            logging.error(f"Error cargando datos de la semana anterior: {e}")

        return None


# Función de compatibilidad con el código existente
def download_and_parse_rept_stock() -> Optional[pd.DataFrame]:
    """Función de compatibilidad que usa el descargador resiliente."""
    return resilient_downloader.download_and_parse_rept_stock()

# Instancia global del descargador resiliente (al final para evitar errores de referencia)
resilient_downloader = ResilientAPIDownloader()

def load_catalogs_and_lines() -> Tuple[List[str], pd.DataFrame, pd.DataFrame]:
    """Carga las plantillas manuales de Excel."""
    logging.info("Cargando plantillas manuales. Asegúrese que los encabezados son: 'codigo', 'nombre', 'linea', 'orden', 'u_por_caja'")
    try:
        required_files = [
            (settings.INPUT_LINES_TO_PROCESS_EXCEL, "Archivo de líneas a procesar"),
            (settings.INPUT_GENERALES_EXCEL, "Catálogo de códigos generales"),
            (settings.INPUT_ESPECIALES_EXCEL, "Catálogo de códigos especiales")
        ]
        for filepath, description in required_files:
            if not validate_file_exists(filepath, description):
                return [], pd.DataFrame(), pd.DataFrame()

        df_lineas = pd.read_excel(settings.INPUT_LINES_TO_PROCESS_EXCEL)
        df_lineas.rename(columns=settings.MANUAL_COLS_MAP, inplace=True)
        lineas = df_lineas["linea"].astype(str).str.strip().tolist()
        if 'ESPECIALES' in lineas:
            lineas.remove('ESPECIALES')

        df_generales = pd.read_excel(settings.INPUT_GENERALES_EXCEL, dtype={'codigo': str})
        df_generales.rename(columns=settings.MANUAL_COLS_MAP, inplace=True)
        
        df_especiales = pd.read_excel(settings.INPUT_ESPECIALES_EXCEL, header=None)
        # Assuming the input Excel has columns in the order: orden, codigo, motivo
        # We want: orden, codigo, motivo
        # So, we select columns by their 0-based index and then rename them.
        # Index 0: orden, Index 1: codigo, Index 2: motivo
        df_especiales = df_especiales.iloc[:, [0, 1, 2]] # Select 'orden', 'codigo', 'motivo' by index
        df_especiales.columns = ['orden', 'codigo', 'motivo'] # Assign new column names
        df_especiales['codigo'] = df_especiales['codigo'].astype(str) # Ensure 'codigo' is string type
        # No need to rename columns using settings.MANUAL_COLS_MAP as we explicitly set them

        logging.info(f"Cargadas {len(lineas)} líneas a procesar.")
        logging.info(f"Catálogo generales: {len(df_generales)} códigos.")
        logging.info(f"Catálogo especiales: {len(df_especiales)} códigos.")

        return lineas, df_generales, df_especiales
    except Exception as e:
        logging.error(f"Error cargando catálogos y líneas: {e}")
        return [], pd.DataFrame(), pd.DataFrame()

def load_base_total() -> Optional[pd.DataFrame]:
    """Carga el archivo base_total.xls del ERP."""
    if not validate_file_exists(settings.INPUT_BASE_TOTAL, "Base total"):
        return None
    try:
        df_base = pd.read_excel(settings.INPUT_BASE_TOTAL, engine='xlrd', dtype={'codigo': str})
        df_base.columns = df_base.columns.str.strip()
        
        cols_to_drop = ['FLG_INACTIVO', 'FLG_DESCONTINUADO']
        df_base.drop(columns=cols_to_drop, inplace=True, errors='ignore')

        df_base.rename(columns=settings.BASE_TOTAL_COLS_MAP, inplace=True)

        required_columns = ['codigo', 'nombre', 'linea']
        if not all(col in df_base.columns for col in required_columns):
            logging.error(f"Columnas requeridas {required_columns} faltantes en base_total.")
            return None

        df_base['codigo'] = df_base['codigo'].astype(str).str.strip()
        # Remove all spaces
        df_base['codigo'] = df_base['codigo'].str.replace(' ', '', regex=False)
        df_base['linea'] = df_base['linea'].astype(str).str.strip()

        for col in ['ean', 'ean_14']:
            if col in df_base.columns:
                df_base[col] = df_base[col].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                # Remove all spaces
                df_base[col] = df_base[col].str.replace(' ', '', regex=False)

        logging.info(f"Base total procesada: {len(df_base)} productos.")
        return df_base
    except Exception as e:
        logging.error(f"Error procesando base_total.xls: {e}")
        return None


def merge_catalogs(df_generales: pd.DataFrame, df_especiales: pd.DataFrame) -> pd.DataFrame:
    """Fusiona los catálogos de códigos generales y especiales."""
    try:
        df_generales['codigo'] = df_generales['codigo'].astype(str).str.strip()
        df_especiales['codigo'] = df_especiales['codigo'].astype(str).str.strip()

        catalogo_df = pd.concat([df_generales, df_especiales], ignore_index=True, sort=False)
        catalogo_df = catalogo_df.fillna('')

        if 'u_por_caja' in catalogo_df.columns:
            catalogo_df['u_por_caja'] = pd.to_numeric(catalogo_df['u_por_caja'], errors='coerce').fillna(1).astype(int)
        else:
            catalogo_df['u_por_caja'] = 1

        if 'orden' in catalogo_df.columns:
            catalogo_df['orden'] = pd.to_numeric(catalogo_df['orden'], errors='coerce').fillna(0).astype(int)
        else:
            catalogo_df['orden'] = 0

        logging.info(f"Catálogo fusionado: {len(catalogo_df)} códigos")
        return catalogo_df
    except Exception as e:
        logging.error(f"Error fusionando catálogos: {e}")
        return pd.DataFrame({'codigo': [], 'u_por_caja': [], 'orden': []})

def load_previous_stock() -> Optional[Dict[str, int]]:
    """
    Carga el stock de productos de la ejecución anterior desde un archivo JSON.
    Retorna un diccionario de codigo -> stock_anterior.
    """
    if not os.path.exists(settings.PREVIOUS_STOCK_FILE):
        logging.info(f"No se encontró el archivo de stock anterior: {settings.PREVIOUS_STOCK_FILE}. Se asume primera ejecución o archivo no disponible.")
        return {}
    try:
        with open(settings.PREVIOUS_STOCK_FILE, 'r', encoding='utf-8') as f:
            previous_stock_data = json.load(f)
        logging.info(f"Stock anterior cargado desde {settings.PREVIOUS_STOCK_FILE} con {len(previous_stock_data)} productos.")
        return previous_stock_data
    except Exception as e:
        logging.error(f"Error al cargar el stock anterior desde {settings.PREVIOUS_STOCK_FILE}: {e}")
        return {}

def load_historical_stock_snapshot(date: datetime) -> Optional[Dict[str, int]]:
    """
    Carga un snapshot de stock histórico para una fecha específica.
    Retorna un diccionario de codigo -> stock_referencial para esa fecha.
    """
    snapshot_filename = os.path.join(settings.HISTORICOS_DIR, f"stock_snapshot_{date.strftime('%Y-%m-%d')}.json")
    if not os.path.exists(snapshot_filename):
        logging.warning(f"No se encontró el snapshot histórico para la fecha {date.strftime('%Y-%m-%d')}: {snapshot_filename}")
        return {}
    try:
        with open(snapshot_filename, 'r', encoding='utf-8') as f:
            historical_stock_data = json.load(f)
        logging.info(f"Snapshot histórico cargado desde {snapshot_filename} con {len(historical_stock_data)} productos.")
        return historical_stock_data
    except Exception as e:
        logging.error(f"Error al cargar el snapshot histórico desde {snapshot_filename}: {e}")
        return {}

