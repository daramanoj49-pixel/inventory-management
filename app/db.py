"""
MongoDB:

MongoDB -> used as the primary source of truth for products.
Connection values are parameterized and passed as environment variables so the same code
can be run locally, in Docker, and in Kubernetes.
"""

import os
from pymongo import MongoClient


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "inventorydb")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]

products_collection = db["products"]