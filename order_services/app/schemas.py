
from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime


# Order Response
class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    payment_status: str
    status: str
    address: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Order Item Response
class OrderitemResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    product_id: int
    product_name: str
    product_image: str
    quantity: int
    price: float
    total_price: float

    model_config = ConfigDict(from_attributes=True)


# Combined Order Response
class OrderCreateResponse(BaseModel):
    order: OrderResponse
    items: List[OrderitemResponse]
