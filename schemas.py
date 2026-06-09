from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = "Друг"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ДОБАВЛЕНО: Схема для обновления профиля
class UserUpdate(BaseModel):
    name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    class Config:
        from_attributes = True

class TransactionCreate(BaseModel):
    amount: float
    category: str = "Разное"

class BudgetUpdate(BaseModel):
    monthly_budget: float
    daily_limit: float

class HabitCreate(BaseModel):
    name: str

class HabitUpdate(BaseModel):
    name: str

class TaskCreate(BaseModel):
    name: str
    type: str = "routine"
    dates: list[str]

class CategoryCreate(BaseModel):
    name: str