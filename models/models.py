"""Esquemas Pydantic de TechGear."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Productos (CRUD) ----------
class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=2)
    descripcion: str = ""
    categoria: str
    precio: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class ProductoCreate(ProductoBase):
    """POST: crear producto (todos los campos requeridos)."""


class ProductoUpdate(BaseModel):
    """PUT: actualizar producto (todos los campos opcionales)."""
    nombre: Optional[str] = Field(None, min_length=2)
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    precio: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)


class ProductoOut(ProductoBase):
    """GET / respuestas: producto con su id."""
    id: str


# ---------- Pedidos (crear y ver) ----------
class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)


class PedidoCreate(BaseModel):
    """POST: lo único que envía el cliente."""
    cliente: str = Field(..., min_length=2)
    items: List[ItemPedido] = Field(..., min_length=1)


class PedidoOut(PedidoCreate):
    """GET / respuestas: pedido con los campos que calcula el servidor."""
    id: str
    total: float
    estado: str
    fecha: datetime


# ---------- Usuarios ----------
class Usuario(BaseModel):
    nombre: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)