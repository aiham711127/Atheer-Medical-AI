# backend/app/models/domain/document.py
import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base

class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    
    # البصمة الرقمية المانعة للتكرار (تمنع رفع نفس الملف مرتين)
    file_hash = Column(String, unique=True, index=True, nullable=False)
    
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    
    # تسجيل الخطأ إن وجد (إلزامي في الأنظمة الإنتاجية)
    error_message = Column(String, nullable=True)
    
    # المفتاح الأجنبي المرتبط بجدول users الذي فحصناه
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # استخدام دالة القاعدة لضمان دقة الوقت
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Document {self.filename} - {self.status}>"

