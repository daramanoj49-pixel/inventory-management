"""
Integration tests for the Inventory Management API.

Test strategy:
- Reset MongoDB before each test.
- Reset Elasticsearch before each test.
- Validate CRUD behavior, Elasticsearch search, analytics, and MongoDB to Elasticsearch sync.
"""

from app.main import create_app
from app.db import products_collection
from app.es import es_client, ES_INDEX


def reset_test_data():
    test_products = [
        {
            "productId": 1,
            "productName": "Essence Mascara Lash Princess",
            "price": 9.99,
            "description": "Popular mascara known for volumizing and lengthening effects.",
            "productCategory": "beauty",
            "availableQuantity": 99
        },
        {
            "productId": 2,
            "productName": "Calvin Klein CK One",
            "price": 49.99,
            "description": "Classic unisex fragrance with a fresh and clean scent.",
            "productCategory": "fragrances",
            "availableQuantity": 29
        },
        {
            "productId": 3,
            "productName": "Dior J'adore",
            "price": 89.99,
            "description": "Luxurious floral fragrance with jasmine and rose notes.",
            "productCategory": "fragrances",
            "availableQuantity": 98
        }
    ]

    products_collection.delete_many({})
    products_collection.insert_many([product.copy() for product in test_products])

    if es_client.indices.exists(index=ES_INDEX):
        es_client.indices.delete(index=ES_INDEX)

    es_client.indices.create(index=ES_INDEX)

    for product in test_products:
        es_client.index(
            index=ES_INDEX,
            id=product["productId"],
            document=product
        )

    es_client.indices.refresh(index=ES_INDEX)


def get_client():
    reset_test_data()
    app = create_app()
    return app.test_client()


def test_health():
    client = get_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_get_products():
    client = get_client()

    response = client.get("/products")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 3


def test_get_product_by_id_success():
    client = get_client()

    response = client.get("/products/1")
    data = response.get_json()

    assert response.status_code == 200
    assert data["productId"] == 1
    assert data["productName"] == "Essence Mascara Lash Princess"


def test_get_product_by_id_not_found():
    client = get_client()

    response = client.get("/products/999999")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}


def test_create_product_success():
    client = get_client()

    new_product = {
        "productId": 999,
        "productName": "Test Bottle",
        "price": 15.99,
        "description": "Reusable bottle for testing.",
        "productCategory": "kitchen-accessories",
        "availableQuantity": 20
    }

    response = client.post("/products", json=new_product)
    data = response.get_json()

    assert response.status_code == 201
    assert data["productId"] == 999
    assert data["productName"] == "Test Bottle"

    search_response = client.get("/products/search?query=reusable")
    search_data = search_response.get_json()

    assert search_response.status_code == 200
    assert any(product["productId"] == 999 for product in search_data)


def test_create_product_duplicate_id():
    client = get_client()

    duplicate_product = {
        "productId": 1,
        "productName": "Duplicate Product",
        "price": 10.99,
        "description": "This should fail.",
        "productCategory": "test-category",
        "availableQuantity": 5
    }

    response = client.post("/products", json=duplicate_product)

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Product with this productId already exists"
    }


def test_create_product_missing_field():
    client = get_client()

    invalid_product = {
        "productId": 1000,
        "productName": "Incomplete Product",
        "price": 9.99
    }

    response = client.post("/products", json=invalid_product)

    assert response.status_code == 400
    assert "Missing required field" in response.get_json()["error"]


def test_update_product_success():
    client = get_client()

    updated_fields = {
        "price": 11.49,
        "availableQuantity": 120,
        "description": "Updated description for testing search sync."
    }

    response = client.put("/products/1", json=updated_fields)
    data = response.get_json()

    assert response.status_code == 200
    assert data["productId"] == 1
    assert data["price"] == 11.49
    assert data["availableQuantity"] == 120
    assert data["description"] == "Updated description for testing search sync."

    search_response = client.get("/products/search?query=sync")
    search_data = search_response.get_json()

    assert search_response.status_code == 200
    assert any(product["productId"] == 1 for product in search_data)


def test_update_product_not_found():
    client = get_client()

    response = client.put("/products/999999", json={"price": 10.99})

    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}


def test_delete_product_success():
    client = get_client()

    response = client.delete("/products/1")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Product deleted successfully"}

    response = client.get("/products/1")
    assert response.status_code == 404

    search_response = client.get("/products/search?query=mascara")
    search_data = search_response.get_json()

    assert search_response.status_code == 200
    assert all(product["productId"] != 1 for product in search_data)


def test_delete_product_not_found():
    client = get_client()

    response = client.delete("/products/999999")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Product not found"}


def test_search_products_success():
    client = get_client()

    response = client.get("/products/search?query=fragrance")
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 2
    assert all("fragrance" in product["description"].lower() for product in data)


def test_search_products_no_match():
    client = get_client()

    response = client.get("/products/search?query=nonexistentkeyword")
    data = response.get_json()

    assert response.status_code == 200
    assert data == []


def test_search_products_missing_query():
    client = get_client()

    response = client.get("/products/search")

    assert response.status_code == 400
    assert response.get_json() == {"error": "Query parameter is required"}


def test_analytics_success():
    client = get_client()

    response = client.get("/products/analytics")
    data = response.get_json()

    assert response.status_code == 200
    assert data["totalProducts"] == 3
    assert data["mostPopularCategory"] == "fragrances"
    assert data["averagePrice"] == 49.99