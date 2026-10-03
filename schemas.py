from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    email: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: str
    password: str

class DonorProfileCreate(BaseModel):
    blood_group: str
    location: str
    availability: bool = True
    last_donation_date: Optional[datetime] = None

class HospitalProfileCreate(BaseModel):
    hospital_name: str
    address: str

class BloodBankProfileCreate(BaseModel):
    bank_name: str
    address: str

class InventoryUpdate(BaseModel):
    blood_group: str
    units: int

class RequestCreate(BaseModel):
    blood_group: str
    units_required: int
    urgency: str
    location: str

class MatchedDonor(BaseModel):
    donor_id: str
    blood_group: str
    location: str
    last_donation: Optional[datetime] = None

class RequestResponse(BaseModel):
    request_id: str
    status: str
    matched_donors: List[MatchedDonor]