from pydantic import BaseModel
from datetime import datetime
class CartRequest(BaseModel):
    product_id : int
    quantity : int

class CartResponse(BaseModel):
    id : int
    user_id : int
    product_id : int
    quantity : int
    created_at : datetime
    
class WishlistResponse(BaseModel):
    id : int
    user_id : int
    product_id : int
    created_at : datetime