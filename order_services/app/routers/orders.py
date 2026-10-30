
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from auth_services.app.auth import get_current_user
from ..models import Order, OrderItems
from ..dependices import getcart, getproduct, getinventory
from ..schemas import OrderCreateResponse

order = APIRouter(prefix="/Order", tags=["Order"])


@order.post("/create-order", response_model=OrderCreateResponse)
def create_order(
    cart_id: int,
    address: str,
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

    
    cart_quantity = cart_response["quantity"]
    available_quantity = inventory_response["available_quantity"]
    product_price = product_response["price"]

    if cart_quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid cart quantity"
        )

    if cart_quantity > available_quantity:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock. Try with a lower quantity."
        )

    
    total_price = product_price * cart_quantity

    try:
        
        new_order = Order(
            user_id=current_user.id,
            total_price=total_price,
            payment_status="Pending",
            status="Pending",
            address=address
        )

        db.add(new_order)
        db.flush()

        
        new_order_item = OrderItems(
            order_id=new_order.id,
            user_id=current_user.id,
            product_id=product_response["id"],
            product_image=product_response["image_url"],
            product_name=product_response["name"],
            quantity=cart_quantity,
            price=product_price,
            total_price=total_price
        )

        db.add(new_order_item)

        
        db.commit()

        db.refresh(new_order)
        db.refresh(new_order_item)

        return {
            "order": new_order,
            "items": [new_order_item]
        }

    except Exception:
        db.rollback()
        raise

@order.get("/get-all-orders", response_model=list[OrderCreateResponse])
def get_all_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    
    orders = db.query(Order).filter(
        Order.user_id == current_user.id
    ).all()

    if not orders:
        raise HTTPException(
            status_code=404,
            detail="No orders found"
        )

    result = []

    
    for order_data in orders:

        order_items = db.query(OrderItems).filter(
            OrderItems.order_id == order_data.id,
            OrderItems.user_id == current_user.id
        ).all()

        
        result.append({
            "order": order_data,
            "items": order_items
        })

    return result
