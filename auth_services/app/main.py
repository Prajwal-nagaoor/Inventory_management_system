from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User
from schemas import RegisterRequest, RegisterResponse
from auth import hashed_password, check_password, storng_password, create_access_token, get_current_user
app = FastAPI()


Base.metadata.create_all(bind=engine)
@app.get("/")
def home():
    return {
        "Message":"fastapi server is running"
    }

@app.post("/register", response_model=RegisterResponse)
def register(regi_data:RegisterRequest,db:Session=Depends(get_db)):
    if not regi_data.username or not regi_data.email or not regi_data.password or not regi_data.first_name or not regi_data.last_name or not regi_data.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All fields must be filled"
        )
    user_exists = db.query(User).filter(
        User.username == regi_data.username
    ).first()

    if user_exists:
        raise HTTPException(
            status_code=400,
            detail="Username alreday exists, try with different username"
        )

    email_exists = db.query(User).filter(
        User.email == regi_data.email
    ).first()


    if email_exists:
        raise HTTPException(
            status_code=400,
            detail="Email is already exists try with different email"
        )

    if not storng_password(regi_data.password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect password farmat\n Your password must contain more then 8 characters\n Your password mush contain atleast on uppercase character\n Your password mush contain atleast on lowercase character\n Your password mush contain atleast on special character[!@#$%^&*]\n "
        )


    new_user = User(
        username = regi_data.username,
        email = regi_data.email,
        first_name = regi_data.first_name,
        last_name = regi_data.last_name,
        role = regi_data.role,
        password = hashed_password(regi_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
@app.post("/login")
def login(username : str, password:str,db:Session=Depends(get_db)):
    if not username or not password:
        raise HTTPException(
            status_code=404,
            detail="All fields must be filled"
        )
    user_exists = db.query(User).filter(
        User.username == username, 
    ).first()

    if not user_exists:
        raise HTTPException(
                    status_code=404,
                    detail="Invalid Username or password"
                )
    password = check_password(
        password,
        user_exists.password
    )

    if not password:
        raise HTTPException(
                    status_code=404,
                    detail="Invalid Username or password"
                )

    access_token = create_access_token(
        {"user_id":user_exists.id,
         "email":user_exists.email,
         "role":user_exists.role}
    )

    return {
        "Message":"User logged in successfully",
        "User_id":user_exists.id,
        "Username":user_exists.username,
        "Email":user_exists.email,
        "access_token":access_token,
        "Role":user_exists.role
    }
@app.get("/profile")
def profile(db:Session=Depends(get_db), current_user:Session=Depends(get_current_user)):
    return {
        "Message":"Profile Details",
        "User_id":current_user.id,
        "username":current_user.username,
        "Email":current_user.email,
        "Role":current_user.role
    }
    
    
