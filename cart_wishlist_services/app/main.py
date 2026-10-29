from fastapi import FastAPI
from .database import Base, engine, get_db
from . import models
Base.metadata.create_all(bind=engine)
from .schemas import CartRequest, CartResponse, WishlistResponse
from auth_services.app.auth import get_current_user
from .router.cart import cart as cart_router
from .router.wishlist import wl as wishlist
app = FastAPI(title="cart and wishlist")
app.include_router(cart_router)
app.include_router(wishlist)
@app.get("/")
def home():
    return {
        "Message":"Cart and withlist server is running"
    }



