# 🎮 TechGear — Tienda Virtual de Tecnología

🖥️ Tienda en línea de tecnología con catálogo de productos, compra directa de un producto (sin carrito), historial de pedidos para el cliente y un panel de administración para gestionar productos, categorías y pedidos.

El proyecto está dividido en dos aplicaciones:

- ⚡ **`techgear_api`**: API REST (FastAPI + MongoDB Atlas) con autenticación JWT.
- 🌐 **`techgear_web`**: sitio web (Django + Bootstrap) que consume la API.

---

## 🛠️ Tecnologías y librerías

| Capa | Tecnología |
|---|---|
| ⚡ API | Python, FastAPI, Uvicorn |
| 🗄️ Base de datos | MongoDB Atlas, PyMongo |
| 📋 Validación | Pydantic (`pydantic[email]`) |
| 🔐 Seguridad | JWT (PyJWT), bcrypt, python-dotenv |
| 🌐 Web | Django, requests |
| 🎨 Interfaz | HTML, Bootstrap 5.3 |
| 🚀 Despliegue | Render (API) |

---

## 📁 Estructura del proyecto

```text
Taller2_API/
│
├── 📁 .vscode/
│
├── 📁 techgear/
│   │
│   ├── 📁 media/
│   │   └── 📁 productos/              # Fotos de productos
│   │       ├── 🖼️ producto_1.jpg
│   │       ├── 🖼️ producto_2.jpg
│   │       ├── 🖼️ producto_3.webp
│   │       └── 🖼️ producto_4.png
│   │
│   ├── 📁 techgear_api/               # API REST con FastAPI
│   │   ├── 📁 db/
│   │   │   └── 🐍 database.py         # Conexión a MongoDB Atlas
│   │   │
│   │   ├── 📁 models/
│   │   │   └── 🐍 models.py           # Esquemas Pydantic
│   │   │
│   │   ├── 🐍 main.py                 # Endpoints de la API
│   │   ├── 🐍 seguridad.py            # JWT y hash de contraseñas
│   │   ├── 📄 requirements.txt
│   │   ├── 🔒 .env                   # Variables de entorno
│   │   └── 📄 .gitignore
│   │
│   ├── 📁 techgear_web/               # Proyecto Django
│   │   │
│   │   ├── 📁 tienda/                 # Aplicación principal
│   │   │   ├── 📁 migrations/         # Migraciones
│   │   │   │   └── 🐍 __init__.py
│   │   │   │
│   │   │   ├── 📁 static/             # Archivos estáticos
│   │   │   │
│   │   │   ├── 📁 templates/
│   │   │   │   └── 📁 tienda/
│   │   │   │       ├── 📄 _estado_badge.html
│   │   │   │       ├── 📄 admin_pedidos.html
│   │   │   │       ├── 📄 base.html
│   │   │   │       ├── 📄 catalogo.html
│   │   │   │       ├── 📄 dashboard.html
│   │   │   │       ├── 📄 login.html
│   │   │   │       ├── 📄 mis_pedidos.html
│   │   │   │       ├── 📄 pedido_confirmacion.html
│   │   │   │       ├── 📄 perfil.html
│   │   │   │       ├── 📄 producto_detalle.html
│   │   │   │       ├── 📄 producto_form.html
│   │   │   │       ├── 📄 registro.html
│   │   │   │       ├── 📄 404.html
│   │   │   │       └── 📄 500.html
│   │   │   │
│   │   │   ├── 🐍 __init__.py
│   │   │   ├── 🐍 apps.py
│   │   │   ├── 🐍 servicios.py        # Cliente HTTP hacia la API
│   │   │   ├── 🐍 urls.py             # Rutas de la tienda
│   │   │   └── 🐍 views.py            # Lógica de las vistas
│   │   │
│   │   ├── 🐍 __init__.py
│   │   ├── 🐍 asgi.py
│   │   ├── 🐍 settings.py             # Configuración Django
│   │   ├── 🐍 urls.py
│   │   ├── 🐍 wsgi.py
│   │   ├── 📄 requirements.txt
│   │   └── 📄 .gitignore
│   │
│   ├── 🗄️ db.sqlite3
│   ├── 🐍 manage.py                   # Administración Django
│   ├── 📄 pyproject.toml
│   └── 📄 REQUIREMENTS.TXT
│
└── 📄 README.md
```

---

## ✨ Funcionalidades

### 👤 Cliente

- 📝 Registro e inicio de sesión.
- 🔎 Catálogo con búsqueda y filtro por categoría.
- 🛍️ Detalle del producto y compra directa: cantidad (limitada al stock), dirección y datos de envío.
- ✅ Confirmación del pedido y página **Mis pedidos**.

### 👨‍💻 Administrador

- 📦 CRUD de productos con foto.
- 📋 Listado de todos los pedidos y cambio de estado (pendiente, enviado, entregado, cancelado).
- 🔄 Al cancelar un pedido, el stock vuelve al producto.

---

## 🔌 Endpoints principales de la API

| Método | Ruta | Acceso |
|---|---|---|
| 🟢 POST | `/usuarios/registro` | Público |
| 🟢 POST | `/usuarios/login` | Público |
| 🔵 GET | `/usuarios/me` | Autenticado |
| 🔵 GET | `/productos`, `/productos/{id}` | Público |
| 🟠 POST / PUT / DELETE | `/productos`, `/productos/{id}` | Admin |
| 🟢 POST | `/pedidos` | Autenticado |
| 🔵 GET | `/pedidos/mios` | Autenticado |
| 🔵 GET | `/pedidos` | Admin |
| 🟠 PUT | `/pedidos/{id}/estado` | Admin |

📚 La documentación interactiva está en `/docs` de la API.

---

## 🛡️ Manejo de errores

- 📦 **Sin stock:** el botón de compra aparece deshabilitado ("Producto agotado"). Si el producto se agota mientras el cliente llena el formulario, la API lo rechaza y la página muestra el stock real actualizado.
- 🔢 **Cantidad inválida:** se valida en el navegador (mínimo 1, máximo el stock) y de nuevo en Django y en la API.
- 🔄 **Descuento de stock atómico:** la API solo descuenta si todavía hay unidades y revierte el stock si algo falla al guardar el pedido.
- ⚠️ **API caída o lenta:** el sitio muestra un mensaje claro en lugar de romperse (tiempo de espera, sin conexión o respuesta inesperada).
- 🗄️ **Base de datos no disponible:** la API responde `503` con un mensaje descriptivo.
- 🔐 **Sesión vencida:** si el JWT expiró, se cierra la sesión y se redirige al login.
- 🛒 **Doble clic al comprar:** el botón se bloquea al enviar para no duplicar pedidos.
- 🚫 **Páginas 404 y 500:** páginas de error personalizadas.

---

## ⚙️ Instalación y ejecución

📌 **Requisitos:** Python 3.12 o superior y una cuenta de MongoDB Atlas.

### 📥 Clonar el repositorio

```bash
git clone https://github.com/bq2203/T2_API.git
cd T2_API
```

### 1️⃣ ⚡ API

```bash
cd techgear/techgear_api

python -m venv venv
venv\Scripts\activate

# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
```

Crea un archivo `.env` en `techgear_api/` (ver `.env.example`) y arranca:

```bash
uvicorn main:app --reload
```

🌐 Queda en `http://127.0.0.1:8000` (documentación en `/docs`).

### 2️⃣ 🌐 Web

En otra terminal, desde la carpeta que contiene `manage.py`:

```bash
cd techgear

pip install django requests

python manage.py runserver 8001
```

🌍 Abre `http://127.0.0.1:8001`.

En `settings.py`, `API_URL` debe apuntar a la API (`http://127.0.0.1:8000` en local o la URL de Render).

---

## 🔑 Variables de entorno (`techgear_api/.env`)

```env
MONGO_USER=braianquintero64_db_user
MONGO_PASSWORD=Braian2203
MONGO_CLUSTER=cluster0.eeigrd2.mongodb.net
MONGO_DB_NAME=techgear
ADMIN_EMAILS=braianquintero64@gmail.com
```

Agrega también las demás variables que lee `db/database.py` y `seguridad.py` (clúster/base de datos y clave secreta del JWT).

🔒 El archivo `.env` está en `.gitignore` y **no se sube al repositorio**.

☁️ En Render se configuran en **Environment**.

---

## 🚀 App desplegada

- ⚡ **API (Render):** [https://t2-api-1.onrender.com](https://t2-api-1.onrender.com)
- 📚 **Documentación:** [https://t2-api-1.onrender.com/docs](https://t2-api-1.onrender.com/docs)
- 💻 **Repositorio:** [https://github.com/bq2203/T2_API](https://github.com/bq2203/T2_API)

> ⚠️ El plan gratuito de Render duerme la API tras un rato sin uso; la primera petición puede tardar cerca de un minuto en responder.

---

## 👨‍💻 Autor

**Braian Quintero** · ADSO · Ambiente 703

🐙 GitHub: [@bq2203](https://github.com/bq2203/T2_API)

---

<p align="center">
  🎮 <strong>TECHGEAR</strong>
  <br>
  <em>El futuro de la tecnología comienza aquí. 🚀</em>
</p>
