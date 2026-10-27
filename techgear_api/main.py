"""API REST de TechGear (FastAPI + MongoDB Atlas)."""
from datetime import datetime
from typing import List

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, status

from db.database import pedidos_collection, productos_collection
from models.models import (
    PedidoCreate,
    PedidoOut,
    ProductoCreate,
    ProductoOut,
    ProductoUpdate,
)

app = FastAPI(title="TechGear API", version="1.0.0")

# uvicorn main:app --reload


def to_oid(id_: str) -> ObjectId:
    try:
        return ObjectId(id_)
    except (InvalidId, TypeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ID inválido")


def serializar(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


# ---------- Productos (CRUD) ----------
@app.post(
    "/productos",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
)
def crear_producto(producto: ProductoCreate):
    res = productos_collection.insert_one(producto.model_dump())
    return serializar(productos_collection.find_one({"_id": res.inserted_id}))


@app.get("/productos", response_model=List[ProductoOut], tags=["Productos"])
def listar_productos():
    return [serializar(p) for p in productos_collection.find()]


@app.get("/productos/{producto_id}", response_model=ProductoOut, tags=["Productos"])
def obtener_producto(producto_id: str):
    producto = productos_collection.find_one({"_id": to_oid(producto_id)})
    if not producto:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return serializar(producto)


@app.put("/productos/{producto_id}", response_model=ProductoOut, tags=["Productos"])
def actualizar_producto(producto_id: str, producto: ProductoUpdate):
    cambios = producto.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No hay campos para actualizar")
    res = productos_collection.update_one(
        {"_id": to_oid(producto_id)}, {"$set": cambios}
    )
    if res.matched_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return serializar(productos_collection.find_one({"_id": to_oid(producto_id)}))


@app.delete("/productos/{producto_id}", tags=["Productos"])
def eliminar_producto(producto_id: str):
    res = productos_collection.delete_one({"_id": to_oid(producto_id)})
    if res.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return {"mensaje": "Producto eliminado"}


# ---------- Pedidos ----------
@app.post(
    "/pedidos",
    response_model=PedidoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Pedidos"],
)
def registrar_pedido(pedido: PedidoCreate):
    total = 0.0
    actualizaciones = []
    for item in pedido.items:
        producto = productos_collection.find_one({"_id": to_oid(item.producto_id)})
        if not producto:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"Producto {item.producto_id} no existe"
            )
        if producto["stock"] < item.cantidad:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Stock insuficiente para '{producto['nombre']}'",
            )
        total += producto["precio"] * item.cantidad
        actualizaciones.append((producto["_id"], item.cantidad))

    for oid, cantidad in actualizaciones:
        productos_collection.update_one({"_id": oid}, {"$inc": {"stock": -cantidad}})

    data = pedido.model_dump()
    data["total"] = round(total, 2)
    data["estado"] = "pendiente"
    data["fecha"] = datetime.now()
    res = pedidos_collection.insert_one(data)
    return serializar(pedidos_collection.find_one({"_id": res.inserted_id}))


@app.get("/pedidos", response_model=List[PedidoOut], tags=["Pedidos"])
def listar_pedidos():
    return [serializar(p) for p in pedidos_collection.find()]