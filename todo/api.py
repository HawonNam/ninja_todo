from ninja import NinjaAPI, Schema
from typing import List, Optional
from datetime import datetime

from .models import Todo
from django.shortcuts import get_object_or_404

api = NinjaAPI()

class TodoSchema(Schema):
    id: int
    title: str
    completed: bool
    due_date: Optional[datetime]
    
@api.get("/todos", response = List[TodoSchema])
def list_todos(request):
    todos = Todo.objects.all()
    return todos

@api.get("/todos/{todo_id}", response = TodoSchema)
def get_todo(request, todo_id: int):
    todo = get_object_or_404(Todo, id = todo_id)
    return todo

class TodoIn(Schema):
    title: str
    completed: bool = False
    due_date: Optional[datetime] = None
    
@api.post("/todos", response = TodoSchema)
def create_todo(request, todo_in: TodoIn):
    todo = Todo.objects.create(**todo_in.dict())
    return todo

@api.put("/todos/{todo_id}", response = TodoSchema)
def update_todo(request, todo_id: int, todo_in: TodoIn):
    todo = get_object_or_404(Todo, id = todo_id)
    for key, value in todo_in.dict().items():
        setattr(todo, key, value)
    todo.save()
    return todo

@api.delete("/todos/{todo_id}", response = TodoSchema)
def delete_todo(request, todo_id: int):
    todo = get_object_or_404(Todo, id = todo_id)
    todo.delete()