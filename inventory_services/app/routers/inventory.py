import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Inventory, InventoryTransaction, StockReservation
from product_services.app.models import Products
from ..schemas import (
    InventoryResponse,
    InventoryCreate,
    StockUpdate,
    StockReservationCreate,
    StockReservationResponse,
    InventoryTransactionResponse,
)
from auth_services.app.auth import get_current_user
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/inventory", tags=["Inventory"])

def expire_reservations(db: Session):
    now = datetime.now(timezone.utc)

    expired_reservations = (
        db.query(StockReservation)
        .filter(
            StockReservation.status == "RESERVED",
            StockReservation.expires_at <= now
        )
        .all()
    )

    for reservation in expired_reservations:
        item = (
            db.query(Inventory)
            .filter(
                Inventory.product_id == reservation.product_id
            )
            .first()
        )

        if item is None:
            continue

        if item.reserved_quantity < reservation.quantity:
            continue

        item.reserved_quantity -= reservation.quantity
        reservation.status = "EXPIRED"
        reservation.released_at = now

        transaction = InventoryTransaction(
            product_id=reservation.product_id,
            transaction_type="EXPIRE",
            quantity=reservation.quantity,
            reason=f"Reservation {reservation.id} expired"
        )

        db.add(transaction)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to release expired reservations"
        )

# --------------------------------------------------
# 1. GET LOW-STOCK INVENTORY
# IMPORTANT: Keep this before /{product_id}
# --------------------------------------------------
@router.get("/low_stock")
def get_low_stock_inventory(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    expire_reservations(db)
    inventory_items = db.query(Inventory).all()
    low_stock_items = []

    for item in inventory_items:
        available_quantity = item.quantity - item.reserved_quantity

        if available_quantity <= item.low_stock_threshold:
            low_stock_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "reserved_quantity": item.reserved_quantity,
                "available_quantity": available_quantity,
                "low_stock_threshold": item.low_stock_threshold,
            })

    return {
        "count": len(low_stock_items),
        "low_stock_items": low_stock_items,
    }


# --------------------------------------------------
# 2. GET ALL INVENTORY
# --------------------------------------------------
@router.get("/", response_model=list[InventoryResponse])
def get_all_inventory(db: Session = Depends(get_db)):
    expire_reservations(db)
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
            ),
        })

    return result


# --------------------------------------------------
# 3. CREATE INVENTORY
# --------------------------------------------------

@router.post("/", response_model=InventoryResponse, status_code=201)
def create_inventory(
    inventory_data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Step 1: Validate the product through Product Service
    try:
        response = httpx.get(
            "http://127.0.0.1:8001/get-id-product",
            params={"p_id": inventory_data.product_id},
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

    # Step 2: Validate stock quantities
    if inventory_data.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Initial stock cannot be negative",
        )

    if inventory_data.low_stock_threshold < 0:
        raise HTTPException(
            status_code=400,
            detail="Low-stock threshold cannot be negative",
        )

    # Step 3: Check for duplicate inventory
    existing_inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == inventory_data.product_id)
        .first()
    )

    if existing_inventory:
        raise HTTPException(
            status_code=409,
            detail="Inventory already exists for this product",
        )

    # Step 4: Create the inventory record
    new_inventory = Inventory(
        product_id=inventory_data.product_id,
        quantity=inventory_data.quantity,
        reserved_quantity=0,
        low_stock_threshold=inventory_data.low_stock_threshold,
    )

    try:
        db.add(new_inventory)
        db.flush()

        # Step 5: Record the initial stock movement
        if inventory_data.quantity > 0:
            transaction = InventoryTransaction(
                product_id=inventory_data.product_id,
                transaction_type="ADD",
                quantity=inventory_data.quantity,
                reason="Initial stock",
                responsible_user_id=getattr(current_user, "id", None),
            )
            db.add(transaction)

        db.commit()
        db.refresh(new_inventory)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to create inventory",
        )

    # Step 6: Return the inventory details
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
        ),
    }



# --------------------------------------------------
# 4. UPDATE STOCK: ADD, DEDUCT OR ADJUST
# --------------------------------------------------
@router.patch("/{product_id}/stock", response_model=InventoryResponse)
def update_stock(
    product_id: int,
    update_data: StockUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found",
        )

    if update_data.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative",
        )

    transaction_type = update_data.transaction_type.upper()

    if transaction_type == "ADD":
        if update_data.quantity == 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity to add must be greater than zero",
            )

        item.quantity += update_data.quantity

    elif transaction_type == "DEDUCT":
        available_quantity = item.quantity - item.reserved_quantity

        if update_data.quantity == 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity to deduct must be greater than zero",
            )

        if update_data.quantity > available_quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient available stock",
            )

        item.quantity -= update_data.quantity

    elif transaction_type == "ADJUST":
        if update_data.quantity < item.reserved_quantity:
            raise HTTPException(
                status_code=400,
                detail="Adjusted stock cannot be less than reserved stock",
            )

        item.quantity = update_data.quantity

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid transaction type. Use ADD, DEDUCT or ADJUST",
        )

    transaction = InventoryTransaction(
        product_id=product_id,
        transaction_type=transaction_type,
        quantity=update_data.quantity,
        reason=update_data.reason or "Stock update",
        responsible_user_id=getattr(current_user, "id", None),
    )

    try:
        db.add(transaction)
        db.commit()
        db.refresh(item)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update stock",
        )

    return {
        "id": item.id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "reserved_quantity": item.reserved_quantity,
        "low_stock_threshold": item.low_stock_threshold,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "available_quantity": item.quantity - item.reserved_quantity,
    }


# --------------------------------------------------
# 5. RESERVE STOCK
# --------------------------------------------------
@router.post(
    "/reservations",
    response_model=StockReservationResponse,
    status_code=201,
)
def reserve_stock(
    reserv_data: StockReservationCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if reserv_data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Reservation quantity must be greater than zero",
        )

    item = (
        db.query(Inventory)
        .filter(Inventory.product_id == reserv_data.product_id)
        .with_for_update()
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found for this product",
        )

    available_stock = item.quantity - item.reserved_quantity

    if reserv_data.quantity > available_stock:
        raise HTTPException(
            status_code=400,
            detail="Insufficient available stock",
        )

    try:
        item.reserved_quantity += reserv_data.quantity

        new_reservation = StockReservation(
    product_id=reserv_data.product_id,
    quantity=reserv_data.quantity,
    order_id=reserv_data.order_id,
    status="RESERVED",
    expires_at=datetime.now(timezone.utc) + timedelta(minutes=1)
)
        db.add(new_reservation)
        db.flush()

        transaction = InventoryTransaction(
            product_id=reserv_data.product_id,
            transaction_type="RESERVE",
            quantity=reserv_data.quantity,
            reason="Stock reserved for order",
            responsible_user_id=getattr(current_user, "id", None),
        )
        db.add(transaction)

        db.commit()
        db.refresh(new_reservation)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to reserve stock",
        )

    return new_reservation


# --------------------------------------------------
# 6. RELEASE RESERVED STOCK
# --------------------------------------------------
@router.post(
    "/reservations/{reservation_id}/release",
    response_model=StockReservationResponse,
)
def release_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    reservation = (
        db.query(StockReservation)
        .filter(StockReservation.id == reservation_id)
        .first()
    )

    if reservation is None:
        raise HTTPException(
            status_code=404,
            detail="Reservation not found",
        )

    if reservation.status != "RESERVED":
        raise HTTPException(
            status_code=400,
            detail="Reservation has already been released",
        )

    item = (
        db.query(Inventory)
        .filter(Inventory.product_id == reservation.product_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found",
        )

    if item.reserved_quantity < reservation.quantity:
        raise HTTPException(
            status_code=400,
            detail="Reserved stock quantity is inconsistent",
        )

    try:
        item.reserved_quantity -= reservation.quantity
        reservation.status = "RELEASED"

        transaction = InventoryTransaction(
            product_id=reservation.product_id,
            transaction_type="RELEASE",
            quantity=reservation.quantity,
            reason="Reservation released",
            responsible_user_id=getattr(current_user, "id", None),
        )
        db.add(transaction)

        db.commit()
        db.refresh(reservation)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to release reservation",
        )

    return reservation


# --------------------------------------------------
# 7. GET TRANSACTION HISTORY FOR A PRODUCT
# --------------------------------------------------
@router.get(
    "/{product_id}/transactions",
    response_model=list[InventoryTransactionResponse],
)
def get_inventory_transaction(
    product_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found for this product",
        )

    transactions = (
        db.query(InventoryTransaction)
        .filter(InventoryTransaction.product_id == product_id)
        .order_by(InventoryTransaction.created_at.desc())
        .all()
    )

    return transactions


# --------------------------------------------------
# 8. GET INVENTORY FOR ONE PRODUCT
# Keep this dynamic route near the bottom.
# --------------------------------------------------
@router.get("/get-inventory/{product_id}", response_model=InventoryResponse)
def get_inventory_by_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    expire_reservations(db)
    item = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found for this product",
        )

    return {
        "id": item.id,
        "product_id": item.product_id,
        "quantity": item.quantity,
        "reserved_quantity": item.reserved_quantity,
        "low_stock_threshold": item.low_stock_threshold,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "available_quantity": item.quantity - item.reserved_quantity,
    }
