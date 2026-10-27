"""Conexión a MongoDB Atlas."""
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pymongo import MongoClient

# Carga techgear_api/.env
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "techgear")

MONGO_URI = (
    f"mongodb+srv://{quote_plus(MONGO_USER)}:{quote_plus(MONGO_PASSWORD)}"
    f"@{MONGO_CLUSTER}/?retryWrites=true&w=majority"
)

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

productos_collection = db["productos"]
pedidos_collection = db["pedidos"]
