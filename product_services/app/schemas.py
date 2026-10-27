from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)
