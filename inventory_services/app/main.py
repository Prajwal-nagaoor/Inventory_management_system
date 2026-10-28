from fastapi import FastAPI
from .models import Inventory, InventoryTransaction
from .database import Base, engine
from .routers.inventory import router as inventory_router
app = FastAPI()
Base.metadata.create_all(bind=engine)

app.include_router(inventory_router)
@app.get("/")
def home():
    return {
        "Message":"inventory services server is running"
    }