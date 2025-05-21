from ninja import NinjaAPI, Schema
from ninja.security import APIKeyHeader
from ninja.errors import HttpError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from typing import List, Optional
from datetime import datetime
import uuid

from .models import Todo, ApiKey

class MyApiKeyAuth(APIKeyHeader):
    param_name = "Api-Key"
    header = "Authorization"

    def authenticate(self, request, key):
        try:
            api_key = ApiKey.objects.select_related('user').get(key=key)
            return api_key.user
        except ApiKey.DoesNotExist:
            return None

api = NinjaAPI(auth=[MyApiKeyAuth()])

class LoginIn(Schema):
    username: str
    password: str

class ApiKeyOut(Schema):
    api_key: uuid.UUID

class TodoSchema(Schema):
    id: int
    title: str
    completed: bool
    due_date: Optional[datetime]

class TodoIn(Schema):
    title: str
    completed: bool = False
    due_date: Optional[datetime] = None

class UserProfileSchema(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    date_joined: datetime
    api_key: uuid.UUID

class UserProfileUpdateSchema(Schema):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class NewApiKeySchema(Schema):
    api_key: uuid.UUID

@api.post("/token", response=ApiKeyOut, auth=None)
def generate_token(request, user_login: LoginIn):
    user = authenticate(
        request,
        username=user_login.username,
        password=user_login.password
    )
    if user:
        api_key, created = ApiKey.objects.get_or_create(user=user)
        return ApiKeyOut(api_key=api_key.key)
    else:
        raise HttpError(status_code=401, message="Invalid username or password")

@api.get("/me", response=UserProfileSchema)
def get_current_user(request):
    user = request.auth
    api_key = ApiKey.objects.get(user=user)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "date_joined": user.date_joined,
        "api_key": api_key.key
    }

@api.put("/me", response=UserProfileSchema)
def update_current_user(request, data: UserProfileUpdateSchema):
    user = request.auth
    for attr, value in data.dict(exclude_unset=True).items():
        setattr(user, attr, value)
    user.save()
    api_key = ApiKey.objects.get(user=user)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "date_joined": user.date_joined,
        "api_key": api_key.key
    }

@api.post("/me/regenerate-key", response=NewApiKeySchema)
def regenerate_api_key(request):
    user = request.auth
    api_key = ApiKey.objects.get(user=user)
    api_key.key = uuid.uuid4()
    api_key.save()
    return {"api_key": api_key.key}


@api.get("/todos", response=List[TodoSchema])
def list_todos(request):
    todos = Todo.objects.filter(owner=request.auth).all()
    return todos

@api.get("/todos/{todo_id}", response=TodoSchema)
def get_todo(request, todo_id: int):
    todo = get_object_or_404(Todo, id=todo_id, owner=request.auth)
    return todo

@api.post("/todos", response=TodoSchema)
def create_todo(request, todo_in: TodoIn):
    todo = Todo.objects.create(**todo_in.dict(), owner=request.auth)
    return todo

@api.put("/todos/{todo_id}", response=TodoSchema)
def update_todo(request, todo_id: int, todo_in: TodoIn):
    todo = get_object_or_404(Todo, id=todo_id, owner=request.auth)
    for key, value in todo_in.dict().items():
        setattr(todo, key, value)
    todo.save()
    return todo

@api.delete("/todos/{todo_id}")
def delete_todo(request, todo_id: int):
    todo = get_object_or_404(Todo, id=todo_id, owner=request.auth)
    todo.delete()
