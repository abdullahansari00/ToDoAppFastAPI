from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_admin: Optional[bool] = False


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None


class User(BaseModel):
    id: int
    username: str
    email: str
    is_admin: bool

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class Task(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool

    class Config:
        from_attributes = True
