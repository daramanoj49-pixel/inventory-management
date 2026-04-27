# Inventory Management System (Flask + MongoDB + Elasticsearch + Kubernetes)

## Overview

This project implements an Inventory Management System with:

-   Flask REST API
-   MongoDB as the primary database (source of truth)
-   Elasticsearch for full-text search
-   Docker for containerization
-   Kubernetes (Minikube) for orchestration

**Recommended way to run: Kubernetes (Minikube)**

------------------------------------------------------------------------

## Prerequisites

### Verify Git

``` bash
git --version
```

### Verify Minikube

``` bash
minikube version
```

### Verify Docker

``` bash
docker --version
```

### Verify Minikube is running

``` bash
minikube status
```

------------------------------------------------------------------------

## Clone Repository

``` bash
git clone <REPO_URL>
cd inventory-management
```

------------------------------------------------------------------------

## Quick Start (Kubernetes - Recommended)

### 1. Start Minikube

``` bash
minikube start --driver=docker
```

### 2. Build Image

``` bash
minikube image build -t inventory-app:latest .
```

### 3. Deploy

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

    Inserted 50 products into MongoDB
    Indexed 50 products into Elasticsearch

⚠️ Only continue after job is complete.

------------------------------------------------------------------------

## Get Application URL

Run in one terminal and KEEP IT OPEN:

``` bash
minikube service inventory-app --url
```

Example:

    http://127.0.0.1:55917

In a second terminal:

``` bash
APP_URL="http://127.0.0.1:55917"
```

------------------------------------------------------------------------

## API Test Commands

### Health

``` bash
curl "$APP_URL/health"
```

### Get Products

``` bash
curl "$APP_URL/products"
```

### Search

``` bash
curl "$APP_URL/products/search?query=fragrance"
```

### Analytics

``` bash
curl "$APP_URL/products/analytics"
```

------------------------------------------------------------------------

## Full CRUD Flow

### Create

``` bash
curl -X POST "$APP_URL/products" \
  -H "Content-Type: application/json" \
  -d '{
    "productId": 999,
    "productName": "Trail Bottle",
    "price": 18.99,
    "description": "Bottle for hiking and camping",
    "productCategory": "outdoor",
    "availableQuantity": 45
  }'
```

### Verify

``` bash
curl "$APP_URL/products/999"
curl "$APP_URL/products/search?query=hiking"
```

### Update

``` bash
curl -X PUT "$APP_URL/products/999" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated bottle for trekking"
  }'
```

### Verify Update

``` bash
curl "$APP_URL/products/search?query=trekking"
```

### Delete

``` bash
curl -X DELETE "$APP_URL/products/999"
```

### Verify Delete

``` bash
curl "$APP_URL/products/999"
curl "$APP_URL/products/search?query=trekking"
```

------------------------------------------------------------------------

## Run Tests

``` bash
python -m pytest -q
```

------------------------------------------------------------------------

## Summary

Flask + MongoDB + Elasticsearch + Docker + Kubernetes
