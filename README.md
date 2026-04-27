# Inventory Management System (Flask + MongoDB + Elasticsearch + Kubernetes)

------------------------------------------------------------------------

## Overview

This project implements an Inventory Management System with:

-   Flask REST API
-   MongoDB (source of truth)
-   Elasticsearch (full-text search)
-   Docker (containerization)
-   Kubernetes via Minikube (orchestration)

**Recommended way to run: Kubernetes (Minikube)**

------------------------------------------------------------------------

## Prerequisites

Verify tools:

``` bash
git --version
docker --version
minikube version
kubectl version --client
```

------------------------------------------------------------------------

## Clone Repository

``` bash
git clone https://github.com/daramanoj49-pixel/inventory-management.git
cd inventory-management
```

------------------------------------------------------------------------

# Quick Start (Kubernetes - Recommended)

## Start Minikube

``` bash
minikube start --driver=docker
```

------------------------------------------------------------------------

## Build Image inside Minikube

``` bash
minikube image build -t inventory-app:latest .
```

------------------------------------------------------------------------

## Deploy Resources

``` bash
kubectl apply -f k8s/
```

------------------------------------------------------------------------

## Wait for Setup Job (IMPORTANT)

``` bash
kubectl get jobs
```

Wait until:

    inventory-setup-job   Complete

Check logs:

``` bash
kubectl logs job/inventory-setup-job
```

Expected:
``` bash
- Mongo populated
- Elasticsearch indexed
```

**Do NOT test APIs before this completes**

------------------------------------------------------------------------

## Get Application URL

Run in one terminal (keep open):

``` bash
minikube service inventory-app --url
```

Example:

    http://127.0.0.1:55917

In another terminal:

``` bash
APP_URL="http://127.0.0.1:55917"
```

------------------------------------------------------------------------

# API Test Commands

``` bash
curl "$APP_URL/health"
curl "$APP_URL/products"
curl "$APP_URL/products/1"
curl "$APP_URL/products/search?query=fragrance"
curl "$APP_URL/products/analytics"
```

------------------------------------------------------------------------

# Full CRUD Flow

## Create

``` bash
curl -X POST "$APP_URL/products" \
  -H "Content-Type: application/json" \
  -d '{
    "productId": 999,
    "productName": "Trail Bottle",
    "price": 18.99,
    "description": "Bottle for hiking",
    "productCategory": "outdoor",
    "availableQuantity": 45
  }'
```

## Verify

``` bash
curl "$APP_URL/products/999"
curl "$APP_URL/products/search?query=hiking"
```

## Update

``` bash
curl -X PUT "$APP_URL/products/999" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated bottle for trekking"}'
```

## Delete

``` bash
curl -X DELETE "$APP_URL/products/999"
```

------------------------------------------------------------------------

# Docker Setup (Optional)

``` bash
docker network create inventory-net

docker run -d --name mongo --network inventory-net -p 27017:27017 mongo:7

docker run -d --name elasticsearch --network inventory-net -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.13.4
```

------------------------------------------------------------------------

# Local Setup (Optional)

``` bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

------------------------------------------------------------------------

# Automated Tests (Optional)

Tests require MongoDB + Elasticsearch running locally.

Use Docker setup above, then run:

``` bash
python -m pytest -q
```

------------------------------------------------------------------------

# Summary

    Flask + MongoDB + Elasticsearch + Docker + Kubernetes
