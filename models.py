from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class DonorProfile(Base):
    __tablename__ = "donor_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    blood_group = Column(String, nullable=False)
    location = Column(String, nullable=False)
    availability = Column(Boolean, default=True)
    last_donation_date = Column(DateTime, nullable=True) # NEW: For 3-month rule

class HospitalProfile(Base):
    __tablename__ = "hospital_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    hospital_name = Column(String, nullable=False)
    address = Column(String, nullable=False)

class BloodBankProfile(Base):
    __tablename__ = "bloodbank_profiles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    bank_name = Column(String, nullable=False)
    address = Column(String, nullable=False)

class BloodInventory(Base):
    __tablename__ = "blood_inventory"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    blood_group = Column(String, nullable=False)
    units_available = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

class BloodRequest(Base):
    __tablename__ = "blood_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    blood_group = Column(String, nullable=False)
    units_required = Column(Integer, nullable=False)
    urgency = Column(String, nullable=False)
    location = Column(String, nullable=False) # Hospital location for matching
    status = Column(String, default="PENDING") # PENDING, MATCHED, FULFILLED
    created_at = Column(DateTime, default=datetime.utcnow)