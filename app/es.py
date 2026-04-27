"""
Elasticsearch:

Elasticsearch -> used for full-text search over product descriptions.The index is synchronized from MongoDB through application write operations.
"""

import os
from elasticsearch import Elasticsearch


ES_HOST = os.getenv("ES_HOST", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "products")

es_client = Elasticsearch(ES_HOST)