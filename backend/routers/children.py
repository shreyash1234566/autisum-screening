from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import uuid
from database import get_db, Child, Doctor

router = APIRouter(prefix="/children", tags=["children"])

class ChildCreate(BaseModel):
    id:          Optional[str] = None
    name:        str = Field(..., min_length=1)
    age_months:  int
    gender:      str
    language:    str = "en"
    doctor_id:   Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()

    @field_validator("age_months")
    @classmethod
    def validate_age(cls, v):
        if v <= 0:
            raise ValueError("Age must be positive")
        if v > 120:
            raise ValueError("Age exceeds maximum screening limit of 120 months")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        supported = {"en", "hi", "ta", "te", "kn", "ml", "mr", "gu", "pa", "bn", "or", "as"}
        if v.lower() not in supported:
            raise ValueError(f"Language '{v}' is not supported")
        return v.lower()

class ChildOut(BaseModel):
    id:          str
    name:        str
    age_months:  int
    gender:      str
    language:    str
    created_at:  datetime

    class Config:
        from_attributes = True

@router.post("", response_model=ChildOut)
def register_child(data: ChildCreate, db: Session = Depends(get_db)):
    if data.doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == data.doctor_id).first()
        if not doctor:
            raise HTTPException(status_code=400, detail="Doctor not found")

    child_id = data.id or str(uuid.uuid4())
    existing = db.query(Child).filter(Child.id == child_id).first()
    if existing:
        return existing
    child = Child(
        id=child_id, name=data.name, age_months=data.age_months,
        gender=data.gender, language=data.language, doctor_id=data.doctor_id,
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    return child

@router.get("/{child_id}", response_model=ChildOut)
def get_child(child_id: str, db: Session = Depends(get_db)):
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(404, "Child not found")
    return child
