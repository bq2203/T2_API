"""Cliente HTTP del frontend hacia la API FastAPI (techgear_api)."""
import requests
from django.conf import settings

TIMEOUT = 8


class ErrorAPI(Exception):
    """La API respondió con error o no está disponible."""

    def __init__(self, mensaje, status=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def _mensaje_error(resp):
    try:
        detalle = resp.json().get("detail")
    except ValueError:
        return f"Error {resp.status_code}"
    if isinstance(detalle, list):  # errores de validación de Pydantic
        return "; ".join(e.get("msg", "dato inválido") for e in detalle)
    return detalle or f"Error {resp.status_code}"


def llamar(metodo, ruta, token=None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.request(
            metodo, f"{settings.API_URL}{ruta}", headers=headers, timeout=TIMEOUT, **kwargs
        )
    except requests.RequestException:
        raise ErrorAPI("No se pudo conectar con la API de TechGear.")
    if not resp.ok:
        raise ErrorAPI(_mensaje_error(resp), resp.status_code)
    return resp.json()


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
