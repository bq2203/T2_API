from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

import uuid
from pathlib import Path

from django.core.files.storage import default_storage
from . import servicios
from .servicios import ErrorAPI


def login_requerido(vista):
    """Protege vistas: exige un JWT guardado en la sesión de Django."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.session.get("token"):
            messages.info(request, "Inicia sesión para continuar.")
            return redirect("login")
        return vista(request, *args, **kwargs)
    return envoltura


def catalogo(request):
    try:
        productos = servicios.listar_productos()
    except ErrorAPI as e:
        messages.error(request, e.mensaje)
        productos = []

    categorias = sorted({p["categoria"] for p in productos})
    categoria = request.GET.get("categoria", "")
    q = request.GET.get("q", "").strip().lower()
    if categoria:
        productos = [p for p in productos if p["categoria"] == categoria]
    if q:
        productos = [
            p for p in productos
            if q in p["nombre"].lower() or q in p.get("descripcion", "").lower()
        ]
    return render(request, "tienda/catalogo.html", {
        "productos": productos,
        "categorias": categorias,
        "categoria_activa": categoria,
        "q": request.GET.get("q", ""),
    })


def registro(request):
    if request.session.get("token"):
        return redirect("catalogo")
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        if password != request.POST.get("password2", ""):
            messages.error(request, "Las contraseñas no coinciden.")
        else:
            try:
                servicios.registrar(nombre, email, password)
            except ErrorAPI as e:
                messages.error(request, e.mensaje)
            else:
                messages.success(request, "Cuenta creada. Ya puedes iniciar sesión.")
                return redirect("login")
        return render(request, "tienda/registro.html", {"nombre": nombre, "email": email})
    return render(request, "tienda/registro.html")


def login(request):
    if request.session.get("token"):
        return redirect("catalogo")
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        try:
            datos = servicios.login(email, request.POST.get("password", ""))
        except ErrorAPI as e:
            messages.error(request, e.mensaje)
            return render(request, "tienda/login.html", {"email": email})
        # Sesión de Django (cookie firmada) que guarda el JWT de la API
        request.session.cycle_key()
        request.session["token"] = datos["access_token"]
        request.session["usuario"] = datos["usuario"]
        messages.success(request, f"Bienvenido, {datos['usuario']['nombre']}.")
        return redirect("catalogo")
    return render(request, "tienda/login.html")


@require_POST
def logout(request):
    request.session.flush()
    messages.info(request, "Sesión cerrada.")
    return redirect("catalogo")


@login_requerido
def perfil(request):
    try:
        usuario = servicios.perfil(request.session["token"])
    except ErrorAPI as e:
        if e.status == 401:  # JWT expirado o inválido
            request.session.flush()
            messages.error(request, "Tu sesión expiró. Inicia sesión de nuevo.")
            return redirect("login")
        messages.error(request, e.mensaje)
        return redirect("catalogo")
    return render(request, "tienda/perfil.html", {"perfil": usuario})

EXT_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FOTO_MB = 2


def _guardar_foto(archivo):
    """Valida y guarda la foto. Devuelve (url, error)."""
    ext = Path(archivo.name).suffix.lower()
    if ext not in EXT_PERMITIDAS:
        return None, "La foto debe ser JPG, PNG o WEBP."
    if archivo.size > MAX_FOTO_MB * 1024 * 1024:
        return None, f"La foto no puede pesar más de {MAX_FOTO_MB} MB."
    nombre = default_storage.save(f"productos/{uuid.uuid4().hex}{ext}", archivo)
    return default_storage.url(nombre), None    

# =====================================================================
# DASHBOARD ADMIN (CRUD de productos)
# El navegador solo sabe enviar GET y POST desde un <form>; Django recibe
# esos POST y los traduce a POST / PUT / DELETE hacia la API de FastAPI.
# =====================================================================
CAMPOS_PRODUCTO = ("nombre", "descripcion", "categoria", "precio", "stock")


def admin_requerido(vista):
    """Exige sesión iniciada Y rol admin (la API vuelve a validarlo con el JWT)."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not request.session.get("token"):
            messages.info(request, "Inicia sesión para continuar.")
            return redirect("login")
        if request.session.get("usuario", {}).get("rol") != "admin":
            messages.error(request, "Solo los administradores pueden entrar al dashboard.")
            return redirect("catalogo")
        return vista(request, *args, **kwargs)
    return envoltura


def _sesion_expirada(request, e):
    """Si la API dijo 401 (JWT vencido) cierra la sesión y manda al login."""
    if e.status == 401:
        request.session.flush()
        messages.error(request, "Tu sesión expiró. Inicia sesión de nuevo.")
        return redirect("login")
    return None


def _leer_formulario(request):
    """Devuelve (valores_crudos, datos_para_la_api, error)."""
    crudos = {c: request.POST.get(c, "").strip() for c in CAMPOS_PRODUCTO}
    try:
        datos = {
            "nombre": crudos["nombre"],
            "descripcion": crudos["descripcion"],
            "categoria": crudos["categoria"],
            "precio": float(crudos["precio"].replace(",", ".")),
            "stock": int(crudos["stock"]),
        }
    except ValueError:
        return crudos, None, "El precio y el stock deben ser números válidos."
    return crudos, datos, None


@admin_requerido
def dashboard(request):
    try:
        productos = servicios.listar_productos()
    except ErrorAPI as e:
        messages.error(request, e.mensaje)
        productos = []
    return render(request, "tienda/dashboard.html", {"productos": productos})


@admin_requerido
def producto_crear(request):
    contexto = {"modo": "crear", "producto": {}}
    if request.method == "POST":
        crudos, datos, error = _leer_formulario(request)
        contexto["producto"] = crudos
        if error:
            messages.error(request, error)
            return render(request, "tienda/producto_form.html", contexto)

        # Foto obligatoria al crear
        foto = request.FILES.get("foto")
        if not foto:
            messages.error(request, "Debes agregar una foto del producto.")
            return render(request, "tienda/producto_form.html", contexto)
        url, error = _guardar_foto(foto)
        if error:
            messages.error(request, error)
            return render(request, "tienda/producto_form.html", contexto)
        datos["imagen"] = url

        try:
            servicios.crear_producto(request.session["token"], datos)           # POST
        except ErrorAPI as e:
            respuesta = _sesion_expirada(request, e)
            if respuesta:
                return respuesta
            messages.error(request, e.mensaje)
            return render(request, "tienda/producto_form.html", contexto)
        messages.success(request, f"Producto '{datos['nombre']}' creado.")
        return redirect("dashboard")
    return render(request, "tienda/producto_form.html", contexto)


@admin_requerido
def producto_editar(request, producto_id):
    contexto = {"modo": "editar", "producto": {}, "producto_id": producto_id}
    if request.method == "POST":
        crudos, datos, error = _leer_formulario(request)
        contexto["producto"] = crudos
        if error:
            messages.error(request, error)
            return render(request, "tienda/producto_form.html", contexto)

        # Foto opcional al editar: si no suben una, se conserva la actual
        foto = request.FILES.get("foto")
        if foto:
            url, error = _guardar_foto(foto)
            if error:
                messages.error(request, error)
                return render(request, "tienda/producto_form.html", contexto)
            datos["imagen"] = url

        try:
            servicios.actualizar_producto(request.session["token"], producto_id, datos)  # PUT
        except ErrorAPI as e:
            respuesta = _sesion_expirada(request, e)
            if respuesta:
                return respuesta
            messages.error(request, e.mensaje)
            return render(request, "tienda/producto_form.html", contexto)
        messages.success(request, f"Producto '{datos['nombre']}' actualizado.")
        return redirect("dashboard")

    try:
        contexto["producto"] = servicios.obtener_producto(producto_id)          # GET
    except ErrorAPI as e:
        messages.error(request, e.mensaje)
        return redirect("dashboard")
    return render(request, "tienda/producto_form.html", contexto)

@admin_requerido
@require_POST
def producto_eliminar(request, producto_id):
    try:
        servicios.eliminar_producto(request.session["token"], producto_id)     # DELETE
    except ErrorAPI as e:
        respuesta = _sesion_expirada(request, e)
        if respuesta:
            return respuesta
        messages.error(request, e.mensaje)
    else:
        messages.success(request, "Producto eliminado.")
    return redirect("dashboard")
