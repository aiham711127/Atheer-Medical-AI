# backend/app/models/domain/user.py
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

# تعريف الأدوار المسموح بها في النظام
class UserRole(str, enum.Enum):
    doctor = "doctor"
    student = "student"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=True)
    
    # الحقل الجديد لتحديد دور المستخدم (افتراضياً: طالب)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.email} - {self.role}>"