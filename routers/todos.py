from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from starlette import status
import models
from models import Todos
from database import SessionLocal
from .auth import get_current_user

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix='/todos',
    tags=['todos'],
    responses={404: {'descriptio': 'Not found'}}
)

templates = Jinja2Templates(directory='templates')
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


@router.get('/test')
def test(request: Request):
    return templates.TemplatesResponse('home.html', {'request': request})

# SELECT * FROM todos
@router.get('/', status_code=status.HTTP_200_OK)
def read_all(db: db_dependency, user: user_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed.')

    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()


# SELECT * FROM todos WHERE id=#
@router.get('/todo/{todo_id}', status_code=status.HTTP_200_OK)
def read_by_id(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):

    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed.')

    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail='Todo not found.')


# INSERT INTO table (...) VALUES (...);
@router.post('/todo', status_code=status.HTTP_201_CREATED)
def create_todo(db: db_dependency, user: user_dependency, todo_request: TodoRequest):

    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed.')

    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get('id'))

    db.add(todo_model)
    db.commit()


#  UPDATE table SET colm_name='...' WHERE id=#;
@router.put('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
def update_todo(db: db_dependency, user: user_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):

    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')
    
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()


# DELETE FROM table WHERE id=#;
@router.delete('/todo/{todo_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(db: db_dependency, user: user_dependency, todo_id: int = Path(gt=0)):
    
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed.')

    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')

    db.query(Todos).filter(Todos.id == todo_id).delete()

    db.commit()