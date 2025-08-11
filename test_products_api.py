#!/usr/bin/env python3
"""
Test script for FlavorForge product API endpoints
"""

import requests
import json

def test_products_api():
    """Test the product endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing FlavorForge Product API...")
    
    # Test 1: Get products (default pagination)
    print("\n1. Testing GET /api/products (default):")
    response = requests.get(f"{base_url}/api/products")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Total items: {data['pagination']['total_items']}")
        print(f"Current page: {data['pagination']['current_page']}")
        print(f"Products returned: {len(data['data'])}")
        if data['data']:
            print(f"First product: {data['data'][0]['name']} (Score: {data['data'][0]['market_score']})")
    else:
        print(f"Error: {response.text}")
    
    # Test 2: Get products with pagination
    print("\n2. Testing GET /api/products with pagination (page=2, limit=5):")
    response = requests.get(f"{base_url}/api/products?page=2&limit=5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Products on page 2: {len(data['data'])}")
        print(f"Page info: {data['pagination']['current_page']}/{data['pagination']['total_pages']}")
    
    # Test 3: Filter by category
    print("\n3. Testing GET /api/products with category filter (Beverages):")
    response = requests.get(f"{base_url}/api/products?category=Beverages")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Beverages found: {len(data['data'])}")
        if data['data']:
            print(f"Sample beverage: {data['data'][0]['name']}")
    
    # Test 4: Search functionality
    print("\n4. Testing GET /api/products with search (Matcha):")
    response = requests.get(f"{base_url}/api/products?search=Matcha")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Matcha products found: {len(data['data'])}")
        for product in data['data']:
            print(f"  - {product['name']} (Score: {product['market_score']})")
    
    # Test 5: Sort by market score
    print("\n5. Testing GET /api/products sorted by market_score:")
    response = requests.get(f"{base_url}/api/products?sort_by=market_score&limit=3")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Top 3 products by market score:")
        for product in data['data']:
            print(f"  - {product['name']}: {product['market_score']}")
    
    # Test 6: Create new product
    print("\n6. Testing POST /api/products (create new product):")
    new_product = {
        "name": "Innovative Moringa Smoothie",
        "category": "Beverages",
        "target_demographics": "26-35",
        "region": "Africa",
        "ingredients": "Moringa, Banana, Honey",
        "flavor_profile": "Herbal, Sweet"
    }
    
    response = requests.post(
        f"{base_url}/api/products",
        json=new_product,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Created product: {data['data']['name']}")
        print(f"Generated market score: {data['data']['market_score']}")
        print(f"Product ID: {data['data']['id']}")
        print(f"Created date: {data['data']['created_date']}")
    else:
        print(f"Error: {response.text}")
    
    # Test 7: Verify new product exists
    print("\n7. Testing if new product appears in list:")
    response = requests.get(f"{base_url}/api/products?search=Moringa")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data['data']:
            print(f"Found new product: {data['data'][0]['name']}")
        else:
            print("New product not found in search")

if __name__ == "__main__":
    try:
        test_products_api()
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running. Please start it with: python main.py")
