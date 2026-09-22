from pydantic import BaseModel

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

class HospitalProfileCreate(BaseModel):
    hospital_name: str
    address: str

class BloodBankProfileCreate(BaseModel):
    bank_name: str
    address: str