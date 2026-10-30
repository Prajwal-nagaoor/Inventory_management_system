from pydantic import BaseModel
from datetime import datetime
class OrderitemResponse(BaseModel):
    id : int
    order_id : int
    user_id : int
    product_id : int
    product_name : str
    product_image:str
    quantity: int
    price : float
    total_price : float
    created_at : datetime


