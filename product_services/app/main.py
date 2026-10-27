from fastapi import FastAPI, Depends, HTTPException, APIRouter, File, Form, UploadFile
from sqlalchemy.orm import Session
from product_services.app.database import Base, engine, get_db
from product_services.app.models import Products
import os
import shutil
from auth_services.app.auth import get_current_user
from product_services.app.schemas import create_product, product_response
app = FastAPI()

Base.metadata.create_all(bind=engine)
@app.get("/")
def home():
    return {
        "Message":"Product server is running successfully"
    }
@app.post("/create-product", response_model=product_response)
def create_product(name : str=Form(...),
                   desc:str=Form(...),
                   price : str=Form(...),
                   category:str=Form(...),
                   brand:str=Form(...),
                   image:UploadFile=File(...),
                   db:Session=Depends(get_db),
                   current_user:Session=Depends(get_current_user)):

    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )
    upload_dir = "media/products"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, image.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    new_product = Products(
        name = name,
        desc = desc,
        price = price,
        category=category,
        brand=brand,
        image_url = file_path
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product
    