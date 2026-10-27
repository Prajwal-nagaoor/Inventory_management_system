from sqlalchemy import Column, String, Integer, DECIMAL, DateTime
from product_services.app.database import Base
from datetime import datetime
class Products(Base):

    __tablename__ = "Products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    desc = Column(String(2000), nullable=False)
    price = Column(DECIMAL(10,2), nullable=False, default=0)
    category = Column(String(200), nullable=False)
    brand = Column(String(200), nullable=False)
    image_url = Column(String(200), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)



