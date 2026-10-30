
from fastapi import HTTPException
import httpx



def getinventory(id: int):
    try:
        inventory_response = httpx.get(
            f"http://127.0.0.1:8002/inventory/get-inventory/{id}",
            timeout=5.0
        )

        # print("Inventory Service Status:", inventory_response.status_code)
        # print("Inventory Service Response:", inventory_response.text)

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Inventory service is unavailable"
        )

    if inventory_response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Inventory item is not found"
        )

    if inventory_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Failed to find inventory item from inventory service"
        )

    return inventory_response.json()



def getproduct(id: int):
    try:
        product_response = httpx.get(
            "http://127.0.0.1:8001/get-id-product",
            params={"p_id": id},
            timeout=5.0
        )
        print("Cart Service Status:", product_response.status_code)
        print("Cart Service Response:", product_response.text)
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Product service is unavailable"
        )

    if product_response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if product_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Failed to validate the product from the product service"
        )

    return product_response.json()



def getcart(id: int, token: str):
    try:
        cart_response = httpx.get(
            "http://127.0.0.1:8003/cart/get-id-cart-item",
            params={"cart_id": id},
            headers={"Authorization": token},
            timeout=5.0
        )
        # print("Cart Service Status:", cart_response.status_code)
        # print("Cart Service Response:", cart_response.text)
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Cart service is unavailable"
        )

    if cart_response.status_code == 401:
        raise HTTPException(
            status_code=401,
            detail="Authentication failed in Cart Service"
        )

    if cart_response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found for this user"
        )

    if cart_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Cart Service error: {cart_response.text}"
        )

    return cart_response.json()
