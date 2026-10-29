from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from .database import Base
from auth_services.app.models import User
from sqlalchemy.sql import func

from sqlalchemy.orm import Relationship

class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    product_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WishList(Base):

    __tablename__ = "wishlist"
    id  = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer,nullable=False, index=True)
    product_id = Column(Integer,nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



