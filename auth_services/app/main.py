from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import Base, engine, get_db
import models
app = FastAPI()


Base.metadata.create_all(bind=engine)
@app.get("/")
def home():
    return {
        "Message":"fastapi server is running"
    }

def register(db:Session=Depends(get_db)):
    pass