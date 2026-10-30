from django.urls import path

from . import views

urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("registro/", views.registro, name="registro"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("perfil/", views.perfil, name="perfil"),
    # Dashboard admin (CRUD productos)
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/nuevo/", views.producto_crear, name="producto_crear"),
    path("dashboard/<str:producto_id>/editar/", views.producto_editar, name="producto_editar"),
    path("dashboard/<str:producto_id>/eliminar/", views.producto_eliminar, name="producto_eliminar"),
]
