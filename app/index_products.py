"""
Rebuild the Elasticsearch product index from MongoDB.

Use this script after seeding MongoDB or whenever Elasticsearch needs to be
rebuilt from the source-of-truth database.
"""

from app.db import products_collection
from app.es import es_client, ES_INDEX


def index_products():
    if es_client.indices.exists(index=ES_INDEX):
        es_client.indices.delete(index=ES_INDEX)

    es_client.indices.create(index=ES_INDEX)

    products = list(products_collection.find())

    for product in products:
        product.pop("_id", None)

        es_client.index(
            index=ES_INDEX,
            id=product["productId"],
            document=product
        )

    es_client.indices.refresh(index=ES_INDEX)

    print(f"Indexed {len(products)} products into Elasticsearch")


if __name__ == "__main__":
    index_products()