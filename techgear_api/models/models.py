"""Esquemas Pydantic de TechGear."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ---------- Productos (CRUD) ----------
class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=2)
    descripcion: str = ""
    categoria: str
    precio: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    imagen: str = ""


class ProductoCreate(ProductoBase):
    """POST: crear producto (todos los campos requeridos)."""


class ProductoUpdate(BaseModel):
    """PUT: actualizar producto (todos los campos opcionales)."""
    nombre: Optional[str] = Field(None, min_length=2)
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    precio: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    imagen: Optional[str] = None  # antes faltaba: por eso la foto no se actualizaba al editar


class ProductoOut(ProductoBase):
    """GET / respuestas: producto con su id."""
    id: str


# ---------- Pedidos ----------
class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)


class DatosEnvio(BaseModel):
    direccion: str = Field(..., min_length=5)
    ciudad: str = Field(..., min_length=2)
    telefono: str = Field(..., min_length=7, max_length=15)
    observaciones: str = ""


class PedidoCreate(BaseModel):
    """POST: lo único que envía el cliente (el usuario sale del token)."""
    items: List[ItemPedido] = Field(..., min_length=1)
    envio: DatosEnvio


class EstadoPedido(BaseModel):
    """PUT /pedidos/{id}/estado (solo admin)."""
    estado: Literal["pendiente", "enviado", "entregado", "cancelado"]


class ItemPedidoOut(ItemPedido):
    nombre: str = ""
    precio_unitario: float = 0.0


class PedidoOut(BaseModel):
    """Respuestas: pedido con lo que calcula el servidor.
    Los campos nuevos son opcionales para que los pedidos viejos no rompan el GET."""
    id: str
    usuario_id: str = ""
    cliente: str = ""
    items: List[ItemPedidoOut]
    envio: Optional[DatosEnvio] = None
    total: float
    estado: str
    fecha: datetime


# ---------- Usuarios ----------
class Usuario(BaseModel):
    """POST /usuarios/registro: lo que envía el cliente."""
    nombre: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class UsuarioLogin(BaseModel):
    """POST /usuarios/login."""
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    """Respuestas: usuario SIN password."""
    id: str
    nombre: str
    email: EmailStr
    rol: str = "cliente"  # "cliente" | "admin"


class Token(BaseModel):
    """Respuesta del login: JWT + datos del usuario."""
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut