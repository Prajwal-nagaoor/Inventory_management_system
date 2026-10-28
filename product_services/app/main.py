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
                   price : float=Form(...),
                   category:str=Form(...),
                   brand:str=Form(...),
                   image:UploadFile=File(...),
                   db:Session=Depends(get_db),
                   current_user:Session=Depends(get_current_user)):
    if current_user.role == "customer":
            raise HTTPException(
                status_code=400,
                detail="You are not allowed to Add the product the product"
            )
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
@app.get("/get-all-product", response_model=list[product_response])
def get_all_product(db:Session=Depends(get_db)):
    products = db.query(Products).all()

    return products
@app.get("/get-id-product", response_model=product_response)
def get_id_product(p_id:int,db:Session=Depends(get_db)):
    product = db.query(Products).filter(
        Products.id == p_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product

@app.put("/update-product",response_model=product_response)
def update_product(id:int=Form(...),
        name : str=Form(...),
                   desc:str=Form(...),
                   price : float=Form(...),
                   category:str=Form(...),
                   brand:str=Form(...),
                   image:UploadFile=File(...),db:Session=Depends(get_db), current_user:Session=Depends(get_current_user)):

    if current_user.role == "customer":
        raise HTTPException(
            status_code=400,
            detail="You are not allowed to update the product"
        )

    product = db.query(Products).filter(
        Products.id == id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )
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

    product.name = name
    product.desc = desc
    product.price = price
    product.category = category
    product.brand = brand
    product.image_url = file_path

    db.commit()
    db.refresh(product)

    return product
@app.delete("/delete-product")
def delete_product(p_id:int,db:Session=Depends(get_db), current_user:Session=Depends(get_current_user)):
    if current_user.role == "customer":
            raise HTTPException(
                status_code=400,
                detail="You are not allowed to Delete the product"
            )
    product = db.query(Products).filter(
        Products.id == p_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "Message":"Product deleted successfully",
        "Product_name ":product.name
    }