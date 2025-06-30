from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import SQLModel, Session, create_engine, select, Field
from pydantic import BaseModel
from typing import Optional
import os
from passlib.context import CryptContext


app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, echo=True)
SQLModel.metadata.create_all(engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_session():
    with Session(engine) as session:
        yield session

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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

    return {"detail": "Login successful"}