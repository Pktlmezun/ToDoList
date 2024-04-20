import uvicorn, os

from sqlalchemy import DateTime
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from database import init_db
from typing import Annotated, Union
from datetime import date

from models.update import UpdateTask
from models.User import User, find_user
from models.Task import Task, CategoryType, TaskStatus, find_task, update
from auth import login_jwt, AuthHandler

app = FastAPI()
auth_handler = AuthHandler()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.get("/")
def home():
    return "Hello World!"


@app.post("/auth/login")
def user_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return login_jwt(form_data)


@app.post("/auth/signup")
def sign_up(username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    if find_user(email) is None:
        new_user = User(username, email, password)
        new_user.add()
    else:
        raise HTTPException(status_code=409, detail="User already exists")


@app.post("/token")
def access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    return login_jwt(form_data)


@app.get("/users/me/info")
def get_info_about_user(token: Annotated[str, Depends(oauth2_scheme)]):
    email = auth_handler.decode_token(token)
    user = find_user(email)
    if user:
        return {"username": user.username,
                "email": user.email
                }


@app.get("/users/me/tasks")
def user_tasks(token: Annotated[str, Depends(oauth2_scheme)]):
    email = auth_handler.decode_token(token)
    user = find_user(email)
    if user:
        return {"tasks": user.all_tasks()}
    else:
        raise HTTPException(status_code=404, detail="User not found!")


@app.patch("/users/me/update_task/{task_id}")
async def update_task(task_id: int, update_data: UpdateTask, token: str = Depends(oauth2_scheme)):
    email = auth_handler.decode_token(token)
    user = find_user(email)
    task = find_task(task_id)
    if user and task and user.id == task.user_id:
        data = update_data.dict(exclude_unset=True)
        update(task_id, data)
        return find_task(task_id).__repr__()
    else:
        raise HTTPException(status_code=404, detail="Not found!")


@app.post("/tasks/new")
def create_task(title: str, description: str, status: TaskStatus, due_date: Union[int, date], category: CategoryType,
                token: Annotated[str, Depends(oauth2_scheme)]):
    if isinstance(due_date, int):
        due_date = date.fromtimestamp(due_date)
    else:
        raise HTTPException(status_code=422, detail="The date format is incorrect!")
    email = auth_handler.decode_token(token)
    user = find_user(email)
    if user:
        new_task = Task(title, description, due_date, status, user.id, category)
        new_task.add()
        raise HTTPException(status_code=200, detail="Successfully added!")
    else:
        raise HTTPException(status_code=404, detail="User not found!")


if __name__ == "__main__":
    # print(find_task(2))
    # update_t = UpdateTask(description="CHANGEEEED")
    # update(2, update_t.dict())
    # print(find_task(2))

    # print(find_task(1))
    init_db()
    uvicorn.run("main:app", host="0.0.0.0", port=os.getenv("PORT", default=8000), log_level="info")
