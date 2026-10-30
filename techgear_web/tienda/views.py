from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

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
