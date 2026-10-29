from fastapi import FastAPI
from .models import Order, OrderItems
from .database import Base, engine

app = FastAPI(title="order management")
Base.metadata.create_all(bind=engine)
@app.get("/")
def home():
    return {
        "Message":"Order server is running"
    }