from pydantic import BaseModel, ConfigDict
from typing import Optional
from decimal import Decimal
from datetime import datetime
class create_product(BaseModel):
    name : str
    desc : str
    price : Decimal
    category:str
    brand:str
class product_response(BaseModel):
    id : int
    name : str
    desc : str
    price : Decimal
    category:str
    brand:str
    created_at:datetime
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
