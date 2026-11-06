"""Cliente HTTP del frontend hacia la API FastAPI (techgear_api)."""
import requests
from django.conf import settings

TIMEOUT = (10, 60)

class ErrorAPI(Exception):
    """La API respondió con error o no está disponible."""
    
    def __init__(self, mensaje, status=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def _mensaje_error(resp):
    try:
        detalle = resp.json().get("detail")
    except (ValueError, AttributeError):
        detalle = None
    if isinstance(detalle, list):  # errores de validación de Pydantic
        return "; ".join(e.get("msg", "dato inválido") for e in detalle)
    if detalle:
        return str(detalle)
    if resp.status_code >= 500:
        return "El servicio no está disponible por ahora. Intenta de nuevo en unos segundos."
    return f"Error {resp.status_code}"
 
 
def llamar(metodo, ruta, token=None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.request(
            metodo, f"{settings.API_URL}{ruta}", headers=headers, timeout=TIMEOUT, **kwargs
        )
    except requests.Timeout:
        raise ErrorAPI("La API tardó demasiado en responder. Intenta de nuevo en unos segundos.")
    except requests.RequestException:
        raise ErrorAPI("No se pudo conectar con la API de TechGear. Intenta más tarde.")
    if not resp.ok:
        raise ErrorAPI(_mensaje_error(resp), resp.status_code)
    try:
        return resp.json()
    except ValueError:
        raise ErrorAPI("La API devolvió una respuesta inesperada.")


def listar_productos():
    return llamar("GET", "/productos")


def registrar(nombre, email, password):
    return llamar(
        "POST", "/usuarios/registro",
        json={"nombre": nombre, "email": email, "password": password},
    )


def login(email, password):
    return llamar("POST", "/usuarios/login", json={"email": email, "password": password})


def perfil(token):
    return llamar("GET", "/usuarios/me", token=token)


# ---------- CRUD de productos (los 4 métodos HTTP hacia FastAPI) ----------
def obtener_producto(producto_id):
    return llamar("GET", f"/productos/{producto_id}")


def crear_producto(token, datos):
    return llamar("POST", "/productos", token=token, json=datos)


def actualizar_producto(token, producto_id, datos):
    return llamar("PUT", f"/productos/{producto_id}", token=token, json=datos)


def eliminar_producto(token, producto_id):
    return llamar("DELETE", f"/productos/{producto_id}", token=token)


def crear_pedido(token, producto_id, cantidad, envio):
    return llamar(
        "POST", "/pedidos", token=token,
        json={
            "items": [{"producto_id": producto_id, "cantidad": cantidad}],
            "envio": envio,
        },
    )


def mis_pedidos(token):
    return llamar("GET", "/pedidos/mios", token=token)

def listar_pedidos(token):
    return llamar("GET", "/pedidos", token=token)


def cambiar_estado_pedido(token, pedido_id, estado):
    return llamar("PUT", f"/pedidos/{pedido_id}/estado", token=token, json={"estado": estado})