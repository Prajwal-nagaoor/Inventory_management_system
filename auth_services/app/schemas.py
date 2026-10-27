from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    username : str
    email : str
    password : str
    first_name : str
    last_name : str
    role : str


class RegisterResponse(BaseModel):
    id : int
    username : str
    email : str
    password : str
    first_name : str
    last_name : str
    role : str
