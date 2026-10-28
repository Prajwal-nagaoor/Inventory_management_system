from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class InventoryCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity:int = Field(default=0, ge=0)
    low_stock_threshold : int = Field(default=5, ge=0)

class InventoryResponse(BaseModel):
    id : int
    product_id : int
    quantity : int
    reserved_quantity : int
    created_at : Optional[datetime] = None
    updated_at : Optional[datetime] = None

    available_quantity : int = 0

    model_config = ConfigDict(from_attributes=True)

class StockUpdate(BaseModel):
    transaction_type : str =Field(...,pattern="^(ADD|DEDUCT|ADJUST)$")
    quantity : int = Field(..., gt=0)
    reason : Optional[str] = None

class StockReservationCreate(BaseModel):
    product_id:int=Field(..., gt=0)
    quantity : int =Field(..., gt=0)
    order_id : Optional[int] = None

class StockReservationResponse(BaseModel):
    id : int
    product_id : int
    quantity : int
    status : str
    order_id : Optional[int]= None
    created_at : Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class InventoryTransactionResponse(BaseModel):
    id : int
    product_id : int
    transaction_type : str
    quantity : int
    reason : Optional[str] = None
    responsible_user_id : Optional[str] = None
    created_at : Optional[datetime] = None

    model_config=ConfigDict(from_attributes=True)