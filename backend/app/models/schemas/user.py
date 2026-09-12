# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from enum import Enum

class UserRoleSchema(str, Enum):
    doctor = "doctor"
    student = "student"

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    specialty: Optional[str] = None
    role: UserRoleSchema = UserRoleSchema.student # إضافة الدور عند التسجيل

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    specialty: Optional[str] = None
    role: UserRoleSchema

    class Config:
        from_attributes = True