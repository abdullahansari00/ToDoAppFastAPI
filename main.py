from datetime import timedelta
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import crud
import schemas
from auth import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_current_user
from crud import verify_password
from database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Management API")


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    db_user = crud.update_user(db, user_id=user_id, user_update=user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    db_user = crud.delete_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}


@app.post("/tasks/", response_model=schemas.Task)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    return crud.create_task(db=db, task=task, user_id=current_user.id)


@app.get("/tasks/", response_model=List[schemas.Task])
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    return crud.get_tasks(db, user_id=current_user.id, skip=skip, limit=limit)


@app.get("/tasks/{task_id}", response_model=schemas.Task)
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if db_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this task")
    return db_task


@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_admin and db_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
    return crud.update_task(db, task_id, task)


@app.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if not current_user.is_admin and db_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    crud.delete_task(db, task_id)
    return {"detail": "Task deleted"}
