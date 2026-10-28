from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Inventory, InventoryTransaction
from ..schemas import InventoryResponse, InventoryCreate, StockUpdate
from auth_services.app.auth import get_current_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])
@router.get("/", response_model=list[InventoryResponse])

@router.get("/", response_model=list[InventoryResponse])
def get_all_inventory(db: Session = Depends(get_db)):
    inventory_items = db.query(Inventory).all()

    result = []

    for item in inventory_items:
        result.append({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "reserved_quantity": item.reserved_quantity,
            "low_stock_threshold": item.low_stock_threshold,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "available_quantity": (
                item.quantity - item.reserved_quantity
            )
        })

    return result
@router.get("/{product_id}", response_model=InventoryResponse)
def get_inventory_by_product(product_id:int, db:Session=Depends(get_db)):
    item = db.query(Inventory).filter(
        Inventory.product_id == product_id
    ).first()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found for this product"
        )

    return {
        "id":item.id,
        "product_id":item.product_id,
        "quantity":item.quantity,
        "reserved_quantity":item.reversed_quantity,
        "low_stock_threshold":item.low_stock_threshold,
        "created_at":item.created_at,
        "updated_at":item.updated_at,
        "available_quantity": (
            item.quantity - item.reversed_quantity
        )
    }


@router.post("/", response_model=InventoryResponse, status_code=201)
def create_inventory(
    inventory_data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    existing_inventory = db.query(Inventory).filter(
        Inventory.product_id == inventory_data.product_id
    ).first()

    if existing_inventory:
        raise HTTPException(
            status_code=400,
            detail="Inventory already exists for this product"
        )

    new_inventory = Inventory(
        product_id=inventory_data.product_id,
        quantity=inventory_data.quantity,
        reserved_quantity=0,
        low_stock_threshold=inventory_data.low_stock_threshold
    )

    try:
        db.add(new_inventory)
        db.flush()

        if inventory_data.quantity > 0:
            transaction = InventoryTransaction(
                product_id=inventory_data.product_id,
                transaction_type="ADD",
                quantity=inventory_data.quantity,
                reason="Initial stock"
            )
            db.add(transaction)

        db.commit()
        db.refresh(new_inventory)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create inventory"
        )

    return {
        "id": new_inventory.id,
        "product_id": new_inventory.product_id,
        "quantity": new_inventory.quantity,
        "reserved_quantity": new_inventory.reserved_quantity,
        "low_stock_threshold": new_inventory.low_stock_threshold,
        "created_at": new_inventory.created_at,
        "updated_at": new_inventory.updated_at,
        "available_quantity": (
            new_inventory.quantity - new_inventory.reserved_quantity
        )
    }

@router.patch("/{product_id}/stock", response_model=InventoryResponse)
def update_stock(product_id:int,update_data:StockUpdate, db:Session=Depends(get_db), current_user:Session=Depends(get_current_user)):
    item = db.query(Inventory).filter(
        Inventory.product_id == product_id
    ).first()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found"
        )
    if update_data.transaction_type == "ADD":
        item.quantity += update_data.quantity
    elif update_data.transaction_type == "DEDUCT":
        available_quantity = item.quantity - item.reversed_quantity

        if update_data.quantity > available_quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient available stock"
            )
        item.quantity -= update_data.quantity
    elif update_data.transaction_type == "ADJUST":
        if update_data.quantity < item.reserved_quantity:
            raise HTTPException(
                status_code=400,
                detail="Adjusted stock cannot be less than reserved stock"
            )

        item.quantity = update_data.quantity

    transaction = InventoryTransaction(
        product_id=product_id,
        transaction_type = update_data.transaction_type,
        quantity= update_data.quantity,
        reason = update_data.reason or "Stock update"
    )

    db.add(transaction)
    db.commit()
    db.refresh(item)

    return {
        "id":item.id,
        "product_id":item.product_id,
        "quantity":item.quantity,
        "reserved_quantity":item.reversed_quantity,
        "low_stock_threshold":item.low_stock_threshold,
        "createt_at":item.created_at,
        "upload_at":item.updated_at,
        "available_quantity":item.quantity - item.reversed_quantity
    }