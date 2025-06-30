from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, create_engine, select, Field
from pydantic import BaseModel
from typing import Optional
import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta


app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "1234567890abcdef1234567890abcdef"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def get_session():
    with Session(engine) as session:
        yield session

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM0)
    return encode_jwt


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(
        select(User).where(User.username == user.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )


    user.password = get_password_hash(user.password)
    db_user = User(username=user.username, password=user.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return UserResponse(id=db_user.id, username=db_user.username)


@app.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    db_user = session.exec(
        select(User).where(User.username == user.username)
    ).first()

    if not db_user or db_user.password != user.password:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    access_token = create_token({"sub": db_user.username})
    return Token(access_token=access_token)