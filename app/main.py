"""
Main Flask application for the Inventory Management System.

Architecture:
- MongoDB is the source of truth for product records.
- Elasticsearch is used for full-text search on product descriptions.

Write flow:
- Create, update, and delete operations modify MongoDB first.
- The same change is then synchronized to Elasticsearch.

Read flow:
- Product CRUD endpoints read from MongoDB.
- Search endpoint reads from Elasticsearch.
- Analytics endpoint uses MongoDB aggregation.

Note:
- refresh=True is used for Elasticsearch writes so changes are immediately
  visible during testing and demos. In production, this would usually be
  handled by Elasticsearch refresh intervals or async indexing.
"""

from flask import Flask, jsonify, request

from app.db import products_collection
from app.es import es_client, ES_INDEX


REQUIRED_FIELDS = [
    "productId",
    "productName",
    "price",
    "description",
    "productCategory",
    "availableQuantity"
]


def serialize_product(product):
    """
    Remove MongoDB's internal _id field before returning product data as JSON.
    """
    product.pop("_id", None)
    return product


def create_app():
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint for local, Docker, and Kubernetes validation."""
        return {"status": "ok"}, 200

    @app.route("/products", methods=["GET"])
    def get_products():
        """Fetch all products from MongoDB."""
        products = list(products_collection.find())
        return jsonify([serialize_product(product) for product in products]), 200

    @app.route("/products/<int:product_id>", methods=["GET"])
    def get_product_by_id(product_id):
        """Fetch a single product by productId from MongoDB."""
        product = products_collection.find_one({"productId": product_id})

        if not product:
            return {"error": "Product not found"}, 404

        return jsonify(serialize_product(product)), 200

    @app.route("/products", methods=["POST"])
    def create_product():
        """
        Create a product in MongoDB and index the same product in Elasticsearch.
        """
        data = request.get_json()

        if not data:
            return {"error": "Request body must be JSON"}, 400

        for field in REQUIRED_FIELDS:
            if field not in data:
                return {"error": f"Missing required field: {field}"}, 400

        existing_product = products_collection.find_one({"productId": data["productId"]})
        if existing_product:
            return {"error": "Product with this productId already exists"}, 400

        products_collection.insert_one(data)

        product_for_response = serialize_product(data.copy())

        es_client.index(
            index=ES_INDEX,
            id=product_for_response["productId"],
            document=product_for_response,
            refresh=True
        )

        return jsonify(product_for_response), 201

    @app.route("/products/<int:product_id>", methods=["PUT"])
    def update_product(product_id):
        """
        Update a product in MongoDB and re-index the updated document in Elasticsearch.
        """
        data = request.get_json()

        if not data:
            return {"error": "Request body must be JSON"}, 400

        existing_product = products_collection.find_one({"productId": product_id})
        if not existing_product:
            return {"error": "Product not found"}, 404

        update_fields = {}
        for field in REQUIRED_FIELDS:
            if field != "productId" and field in data:
                update_fields[field] = data[field]

        if update_fields:
            products_collection.update_one(
                {"productId": product_id},
                {"$set": update_fields}
            )

        updated_product = products_collection.find_one({"productId": product_id})
        product_for_response = serialize_product(updated_product)

        es_client.index(
            index=ES_INDEX,
            id=product_for_response["productId"],
            document=product_for_response,
            refresh=True
        )

        return jsonify(product_for_response), 200

    @app.route("/products/<int:product_id>", methods=["DELETE"])
    def delete_product(product_id):
        """
        Delete a product from MongoDB and remove the corresponding document
        from Elasticsearch.
        """
        result = products_collection.delete_one({"productId": product_id})

        if result.deleted_count == 0:
            return {"error": "Product not found"}, 404

        if es_client.exists(index=ES_INDEX, id=product_id):
            es_client.delete(index=ES_INDEX, id=product_id, refresh=True)

        return {"message": "Product deleted successfully"}, 200

    @app.route("/products/search", methods=["GET"])
    def search_products():
        """
        Full-text search endpoint.

        Searches product descriptions using Elasticsearch.
        """
        query = request.args.get("query")

        if not query:
            return {"error": "Query parameter is required"}, 400

        result = es_client.search(
            index=ES_INDEX,
            query={
                "match": {
                    "description": query
                }
            }
        )

        products = [hit["_source"] for hit in result["hits"]["hits"]]

        return jsonify(products), 200

    @app.route("/products/analytics", methods=["GET"])
    def get_analytics():
        """
        Product analytics endpoint.

        Uses MongoDB aggregation to calculate:
        - total product count
        - most common product category
        - average product price
        """
        total_products = products_collection.count_documents({})

        if total_products == 0:
            return {
                "totalProducts": 0,
                "mostPopularCategory": None,
                "averagePrice": 0.0
            }, 200

        avg_result = list(products_collection.aggregate([
            {
                "$group": {
                    "_id": None,
                    "averagePrice": {"$avg": "$price"}
                }
            }
        ]))

        category_result = list(products_collection.aggregate([
            {
                "$group": {
                    "_id": "$productCategory",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]))

        average_price = avg_result[0]["averagePrice"] if avg_result else 0.0
        most_popular_category = category_result[0]["_id"] if category_result else None

        return {
            "totalProducts": total_products,
            "mostPopularCategory": most_popular_category,
            "averagePrice": round(average_price, 2)
        }, 200

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)