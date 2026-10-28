from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from .database import Base
from sqlalchemy.sql import func

class Inventory(Base):

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer,unique=True,nullable=False, index=True)
    quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())



class InventoryTransaction(Base):

    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True,index=True)
    product_id = Column(Integer,index=True, nullable=False)
    transaction_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    responsible_user_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

        
    

