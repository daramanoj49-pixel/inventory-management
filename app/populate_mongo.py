"""
Seed MongoDB with sample product data.

This script is used for local setup, Docker testing, and resetting development data.
It loads products from app/seed_products.json and inserts them into MongoDB.
"""

import json

from app.db import products_collection


def populate_mongo():
    with open("app/seed_products.json") as f:
        products = json.load(f)

    products_collection.delete_many({})
    products_collection.insert_many(products)

    print(f"Inserted {len(products)} products into MongoDB")


if __name__ == "__main__":
    populate_mongo()