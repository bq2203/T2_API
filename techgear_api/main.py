"""API REST de TechGear (FastAPI + MongoDB Atlas)."""
from datetime import datetime
from typing import List

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.errors import DuplicateKeyError, PyMongoError

from db.database import pedidos_collection, productos_collection, usuarios_collection
from models.models import (
    EstadoPedido,
    PedidoCreate,
    PedidoOut,
    ProductoCreate,
    ProductoOut,
    ProductoUpdate,
    Token,
    Usuario,
    UsuarioLogin,
    UsuarioOut,
)
from seguridad import (
    crear_token,
    decodificar_token,
    es_email_admin,
    hashear_password,
    verificar_password,
)

app = FastAPI(title="TechGear API", version="1.2.0")
bearer = HTTPBearer(auto_error=False)

@app.exception_handler(PyMongoError)
async def error_base_de_datos(request: Request, exc: PyMongoError):
    """Si MongoDB Atlas no responde, el cliente recibe un 503 claro (no un 500 genérico)."""
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Base de datos no disponible. Intenta de nuevo en un momento."},
    )


@app.on_event("startup")
def crear_indices():
    # Un email = una cuenta (lo garantiza MongoDB, no solo el código)
    usuarios_collection.create_index("email", unique=True)

# uvicorn main:app --reload


def to_oid(id_: str) -> ObjectId:
    try:
        return ObjectId(id_)
    except (InvalidId, TypeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ID inválido")


def serializar(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


def usuario_publico(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "nombre": doc["nombre"],
        "email": doc["email"],
        "rol": doc.get("rol", "cliente"),
    }


def usuario_actual(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """Dependencia: exige 'Authorization: Bearer <jwt>' y devuelve el usuario."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token")
    user_id = decodificar_token(cred.credentials)
    usuario = usuarios_collection.find_one({"_id": to_oid(user_id)})
    if not usuario:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario no existe")
    return usuario


def solo_admin(usuario: dict = Depends(usuario_actual)) -> dict:
    """Dependencia: deja pasar únicamente a usuarios con rol 'admin'."""
    if usuario.get("rol") != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere rol de administrador")
    return usuario


# ---------- Productos (CRUD) ----------
@app.post(
    "/productos",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
)
def crear_producto(producto: ProductoCreate, _: dict = Depends(solo_admin)):
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
def actualizar_producto(
    producto_id: str, producto: ProductoUpdate, _: dict = Depends(solo_admin)
):
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
def eliminar_producto(producto_id: str, _: dict = Depends(solo_admin)):
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
def registrar_pedido(pedido: PedidoCreate, usuario: dict = Depends(usuario_actual)):
    total = 0.0
    items_guardar = []
    reservados = []  # (oid, cantidad) ya descontados, para revertir si algo falla

    for item in pedido.items:
        producto = productos_collection.find_one({"_id": to_oid(item.producto_id)})
        if not producto:
            _revertir_stock(reservados)
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"Producto {item.producto_id} no existe"
            )
        res = productos_collection.update_one(
            {"_id": producto["_id"], "stock": {"$gte": item.cantidad}},
            {"$inc": {"stock": -item.cantidad}},
        )
        if res.modified_count == 0:
            _revertir_stock(reservados)
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Stock insuficiente para '{producto['nombre']}'",
            )
        reservados.append((producto["_id"], item.cantidad))
        total += producto["precio"] * item.cantidad
        items_guardar.append({
            "producto_id": item.producto_id,
            "cantidad": item.cantidad,
            "nombre": producto["nombre"],
            "precio_unitario": producto["precio"],
        })

    data = {
        "usuario_id": str(usuario["_id"]),
        "cliente": usuario["nombre"],
        "items": items_guardar,
        "envio": pedido.envio.model_dump(),
        "total": round(total, 2),
        "estado": "pendiente",
        "fecha": datetime.now(),
    }
    try:
        res = pedidos_collection.insert_one(data)
    except PyMongoError:
        _revertir_stock(reservados)
        raise
    return serializar(pedidos_collection.find_one({"_id": res.inserted_id}))


def _revertir_stock(reservados):
    for oid, cantidad in reservados:
        productos_collection.update_one({"_id": oid}, {"$inc": {"stock": cantidad}})


@app.get("/pedidos/mios", response_model=List[PedidoOut], tags=["Pedidos"])
def mis_pedidos(usuario: dict = Depends(usuario_actual)):
    docs = pedidos_collection.find({"usuario_id": str(usuario["_id"])}).sort("fecha", -1)
    return [serializar(p) for p in docs]



@app.get("/pedidos", response_model=List[PedidoOut], tags=["Pedidos"])
def listar_pedidos(_: dict = Depends(solo_admin)):
    return [serializar(p) for p in pedidos_collection.find().sort("fecha", -1)]


@app.put("/pedidos/{pedido_id}/estado", response_model=PedidoOut, tags=["Pedidos"])
def cambiar_estado_pedido(
    pedido_id: str, datos: EstadoPedido, _: dict = Depends(solo_admin)
):
    pedido = pedidos_collection.find_one({"_id": to_oid(pedido_id)})
    if not pedido:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")

    anterior = pedido.get("estado")
    if anterior == "cancelado":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Un pedido cancelado no se puede modificar"
        )

    # Al cancelar, el stock vuelve al producto
    if datos.estado == "cancelado":
        for it in pedido.get("items", []):
            productos_collection.update_one(
                {"_id": to_oid(it["producto_id"])}, {"$inc": {"stock": it["cantidad"]}}
            )

    pedidos_collection.update_one(
        {"_id": pedido["_id"]}, {"$set": {"estado": datos.estado}}
    )
    return serializar(pedidos_collection.find_one({"_id": pedido["_id"]}))

# ---------- Usuarios (registro, login con JWT, perfil) ----------
@app.post(
    "/usuarios/registro",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
)
def registrar_usuario(usuario: Usuario):
    doc = {
        "nombre": usuario.nombre,
        "email": usuario.email.lower(),
        "password": hashear_password(usuario.password),
        "rol": "admin" if es_email_admin(usuario.email) else "cliente",
    }
    try:
        res = usuarios_collection.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status.HTTP_409_CONFLICT, "El email ya está registrado")
    return usuario_publico(usuarios_collection.find_one({"_id": res.inserted_id}))


@app.post("/usuarios/login", response_model=Token, tags=["Usuarios"])
def login(datos: UsuarioLogin):
    usuario = usuarios_collection.find_one({"email": datos.email.lower()})
    if not usuario or not verificar_password(datos.password, usuario["password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email o contraseña incorrectos")
    if es_email_admin(usuario["email"]) and usuario.get("rol") != "admin":
        usuarios_collection.update_one({"_id": usuario["_id"]}, {"$set": {"rol": "admin"}})
        usuario["rol"] = "admin"
    return {
        "access_token": crear_token(str(usuario["_id"])),
        "token_type": "bearer",
        "usuario": usuario_publico(usuario),
    }


@app.get("/usuarios/me", response_model=UsuarioOut, tags=["Usuarios"])
def mi_perfil(usuario: dict = Depends(usuario_actual)):
    return usuario_publico(usuario)
