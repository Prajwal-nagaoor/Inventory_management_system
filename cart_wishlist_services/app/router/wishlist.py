from fastapi import APIRouter, Depends, HTTPException
from ..database import get_db
from ..schemas import  WishlistResponse
from ..models import WishList
from auth_services.app.auth import get_current_user
from sqlalchemy.orm import Session
import httpx

wl = APIRouter(prefix="/wishlist", tags=["wishlist"])

@wl.post("/add-wishlist", response_model=WishlistResponse)
def add_wishlist(product_id:int, db:Session=Depends(get_db), current_user = Depends(get_current_user)):
    if current_user.role != "customer":
        raise HTTPException(
            status_code=400,
            detail="You are not allowd to add wishlist only customer are allowed"
        )

    try:
        response = httpx.get(
            "http://127.0.0.1:8001/get-id-product",
            params={"p_id":product_id},
            timeout=5.0
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="Product service is unavaible"
        )
    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Failed to validate the product with product id"
        )

    wl_item = db.query(WishList).filter(
        WishList.product_id == product_id,
        WishList.user_id == current_user.id
    ).first()

    if wl_item :
        raise HTTPException(
            status_code=400,
            detail="This product is already in wishlist"
        )

    new_wishlist = WishList(
        user_id = current_user.id,
        product_id = product_id

    )

    db.add(new_wishlist)
    db.commit()
    db.refresh(new_wishlist)

    return new_wishlist

@wl.get("/all-wishlist", response_model=list[WishlistResponse])
def get_all_wishlist(db:Session=Depends(get_db), current_user=Depends(get_current_user)):
    wl_items = db.query(WishList).filter(
        WishList.user_id == current_user.id
    ).all()

    if wl_items is None:
        raise HTTPException(
            status_code=400,
            detail="Your wishlist is empty"
        )

    return wl_items

@wl.delete("remove-wishlist")
def remove_wishlist(wl_id:int, db:Session=Depends(get_db), current_user=Depends(get_current_user)):
    if current_user.role != "customer":
        raise HTTPException(
            status_code=400,
            detail="You are not allowd to add wishlist only customer are allowed"
        )
    
    wl_item = db.query(WishList).filter(
        WishList.id == wl_id,
        WishList.user_id == current_user.id

    ).first()

    if wl_item is None:
        raise HTTPException(
            status_code=404,
            detail="Wishlist item is not found"
        )

    db.delete(wl_item)
    db.commit()

    return {
        "Message":"This item is removed from the wishlist"
    }