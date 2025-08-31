from pydantic import BaseModel
from typing import Dict

class AlmacenStock(BaseModel):
    """Define la estructura del stock para un único almacén."""
    total: int
    disponible: int

class ProductoStock(BaseModel):
    """Define el esquema completo para un producto en stock_generales.json."""
    codigo: str
    nombre: str
    linea: str
    ean: str
    ean_14: str
    precio: float
    can_kg_um: float
    u_por_caja: int
    stock_referencial: int
    almacenes: Dict[str, AlmacenStock]
