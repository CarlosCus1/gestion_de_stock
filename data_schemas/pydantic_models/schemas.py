
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ColorStock(BaseModel):
    color: str
    unidades: int

class AlmacenStock(BaseModel):
    total: int
    disponible: int

class ProductoStock(BaseModel):
    codigo: str
    nombre: str
    linea: str
    ean: str = ''
    ean_14: str = ''
    precio: float = 0.0
    can_kg_um: float = 0.0
    u_por_caja: int = 1
    stock_referencial: int = 0
    almacenes: Dict[str, AlmacenStock] = Field(default_factory=dict)
    colores: List[ColorStock] = Field(default_factory=list)

