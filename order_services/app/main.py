from fastapi import FastAPI, HTTPException
from .models import Order, OrderItems
from .database import Base, engine
import httpx
from .routers.orders import order as order_route
app = FastAPI(title="order management")
app.include_router(order_route)
Base.metadata.create_all(bind=engine)
@app.get("/")
def home():
    return {
        "Message":"Order server is running"
    }
