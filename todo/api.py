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

api = NinjaAPI(auth=[MyApiKeyAuth()])  # ✅ 먼저 선언해야 데코레이터에 쓸 수 있음

# === 스키마 정의 ===
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

# === 엔드포인트 정의 ===

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

@api.get("/todos", response=List[TodoSchema])
def list_todos(request):
    # 인증 성공 시 request.auth 에 User 객체가 담깁니다.
    # 이제 현재 로그인한 사용자의 할 일만 필터링해서 반환합니다.
    todos = Todo.objects.filter(owner=request.auth).all()
    return todos # django-ninja가 QuerySet을 받으면 자동으로 Schema 리스트로 변환 시도

# 특정 할 일 하나 가져오기 (인증 및 권한 적용)
# {todo_id: int} 로 경로 파라미터 받기
@api.get("/todos/{todo_id}", response=TodoSchema)
def get_todo(request, todo_id: int):
    # todo_id와 현재 로그인한 사용자를 기준으로 특정 Todo 객체 찾기
    # 해당 사용자의 할 일이 아니거나 없으면 404 Not Found 에러 발생
    todo = get_object_or_404(Todo, id=todo_id, owner=request.auth)
    return todo # django-ninja가 모델 객체를 받으면 자동으로 Schema로 변환 시도

# --- POST Endpoint (할 일 생성 - 인증 적용) ---
# 새로운 할 일 생성
@api.post("/todos", response=TodoSchema)
def create_todo(request, todo_in: TodoIn):
    # todo_in.dict() 와 함께 owner=request.auth 를 추가하여 현재 사용자로 설정
    todo = Todo.objects.create(**todo_in.dict(), owner=request.auth)
    return todo # 생성된 객체를 반환하면 django-ninja가 TodoSchema로 변환

# --- PUT/PATCH Endpoint (할 일 수정 - 인증 및 권한 적용) ---
# 할 일 수정 (인증된 사용자의 할 일 중 해당 ID의 할 일만 수정)
@api.put("/todos/{todo_id}", response=TodoSchema)
def update_todo(request, todo_id: int, todo_in: TodoIn):
    # todo_id와 현재 사용자를 기준으로 수정할 할 일 찾기
    todo = get_object_or_404(Todo, id=todo_id, owner=request.auth)
    # todo_in.dict() 의 내용을 todo 객체에 업데이트
    for key, value in todo_in.dict().items():
        setattr(todo, key, value) # 객체의 속성(key)에 값(value) 설정
    todo.save() # 데이터베이스에 저장
    return todo # 수정된 객체를 반환

# --- DELETE Endpoint (할 일 삭제 - 인증 및 권한 적용) ---
# 할 일 삭제 (인증된 사용자의 할 일 중 해당 ID의 할 일만 삭제)
@api.delete("/todos/{todo_id}")
def delete_todo(request, todo_id: int):
    # todo_id와 현재 사용자를 기준으로 삭제할 할 일 찾기
    todo = get_object_or_404(Todo, id=todo_id, owner=request.auth)
    todo.delete() # 삭제
