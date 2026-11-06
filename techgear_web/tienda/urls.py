from django.urls import path
from . import views

urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("registro/", views.registro, name="registro"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout, name="logout"),
    path("perfil/", views.perfil, name="perfil"),

    # Compra directa y pedidos del cliente
    path("producto/<str:producto_id>/", views.producto_detalle, name="producto_detalle"),
    path("producto/<str:producto_id>/comprar/", views.comprar, name="comprar"),
    path("pedido/confirmacion/", views.pedido_confirmacion, name="pedido_confirmacion"),
    path("mis-pedidos/", views.mis_pedidos, name="mis_pedidos"),

    # Dashboard admin (CRUD productos)
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/nuevo/", views.producto_crear, name="producto_crear"),
    path("dashboard/<str:producto_id>/editar/", views.producto_editar, name="producto_editar"),
    path("dashboard/<str:producto_id>/eliminar/", views.producto_eliminar, name="producto_eliminar"),

    # Dashboard admin (pedidos)
    path("dashboard/pedidos/", views.admin_pedidos, name="admin_pedidos"),
    path("dashboard/pedidos/<str:pedido_id>/estado/", views.admin_pedido_estado, name="admin_pedido_estado"),
]