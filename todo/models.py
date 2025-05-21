from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Todo(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.owner.username}'s Todo: {self.title}"

import uuid

class ApiKey(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s API Key"
    
from django.contrib import admin
admin.site.register(ApiKey)
