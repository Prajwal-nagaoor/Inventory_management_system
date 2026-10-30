from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import Base, engine, get_db
from ..models import Cart, WishList
from ..schemas import CartResponse, CartRequest, WishlistResponse
from auth_services.app.auth import get_current_user
from product_services.app.models import Products
import httpx
from datetime import datetime
cart = APIRouter(prefix="/cart", tags=["cart"])


@cart.post("/add-cart", response_model=CartResponse)
def add_cart(
    cart_data: CartRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "customer":
        raise HTTPException(
            status_code=400,
            detail="You are not allowd to add create cart only customer are allowed"
        )
    # Validate quantity
    if cart_data.quantity < 1:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be at least 1"
        )

    # Check product through Product Service
    try:
        response = httpx.get(
            "http://127.0.0.1:8001/get-id-product",
            params={"p_id": cart_data.product_id},
            timeout=5.0,
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Product Service is unavailable",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Failed to validate product with Product Service",
        )
    # Find existing cart item
    cart_item_exists = db.query(Cart).filter(
        Cart.product_id == cart_data.product_id,
        Cart.user_id == current_user.id
    ).first()

    try:
        if cart_item_exists:
            # Update existing cart item
            cart_item_exists.quantity = cart_data.quantity
        else:
            # Create new cart item
            new_cart = Cart(
                user_id=current_user.id,
                product_id=cart_data.product_id,
                quantity=cart_data.quantity
            )
            db.add(new_cart)

        db.commit()

        if cart_item_exists:
            db.refresh(cart_item_exists)
            return cart_item_exists

        db.refresh(new_cart)
        return new_cart

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to add product to cart"
        )
@cart.get("/get-id-cart-item", response_model=CartResponse)
def get_id_cart_item(
    cart_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    cart_item = db.query(Cart).filter(
        Cart.id == cart_id,
        Cart.user_id == current_user.id
    ).first()

    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item not found"
        )

    return cart_item
@cart.get("/all-cart-item", response_model=list[CartResponse])
def get_all_cart_items(db:Session=Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "customer":
        raise HTTPException(
            status_code=400,
            detail="You are not allowd to add wishlist only customer are allowed"
        )
    cart_item = db.query(Cart).filter(
        Cart.user_id == current_user.id
    ).all()
    if cart_item is None:
        raise HTTPException(
            status_code=400,
            detail="Cart is Empty"
        )

    return cart_item

@cart.patch("/update-cart", response_model=CartResponse)
def update_cart(cart_id:int, quantity:int, db:Session=Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "customer":
        raise HTTPException(
            status_code=400,
            detail="You are not allowd to add update cart only customer are allowed"
        )
    cart_item = db.query(Cart).filter(
        Cart.id == cart_id,
        Cart.user_id == current_user.id
    ).first()

    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item is not found"
        )
    if quantity < 1:
        raise HTTPException(
            status_code=400,
            detail="quantity must be greater then 0"
        )

    cart_item.quantity = quantity
    db.commit()
    db.refresh(cart_item)

    return cart_item

@cart.delete("/delete-cart-item")
def delete_cart_item(cart_id:int,db:Session=Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "customer":
        raise HTTPException(
            status_code=400,
            detail="You are not allowd to add delete cart only customer are allowed"
        )
    cart_item = db.query(Cart).filter(
        Cart.id == cart_id,
        Cart.user_id == current_user.id 
    ).first()

    if cart_item is None:
        raise HTTPException(
            status_code=404,
            detail="Cart item is not found"
        )

    db.delete(cart_item)
    db.commit()

    return {
        "Message":f"Cart Items {cart_item.id} got deleted successfully" 
    }

    