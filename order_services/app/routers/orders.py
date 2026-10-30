from fastapi import APIRouter, Depends, HTTPException, Request
from ..database import get_db
from sqlalchemy.orm import Session
from auth_services.app.auth import get_current_user
from ..models import Order, OrderItems
from ..dependices import getcart,getproduct,getinventory

order = APIRouter(prefix="/Order", tags=["Order"])
@order.get("/get-details")
def create_order(
    cart_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    token = request.headers.get("Authorization")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authorization token is missing"
        )

    cart_response = getcart(cart_id, token)

    product_response = getproduct(cart_response["product_id"])

    inventory_response = getinventory(cart_response["product_id"])

    print("Cart:", cart_response)
    print("Product:", product_response)
    print("Inventory:", inventory_response)

    return {"message": "All services connected successfully"}
