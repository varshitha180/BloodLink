from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import bcrypt
import jwt
from datetime import datetime, timedelta
from database import engine, Base, get_db
import models, schemas
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "bloodlink_super_secret_key_123"
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

security = HTTPBearer()
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None: raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None: raise HTTPException(status_code=401, detail="User not found")
    return user

@app.get("/")
def read_root():
    return {"message": "BloodLink AI Server is Running!"}

# --- AUTH ROUTES ---
@app.post("/api/v1/auth/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user: raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pwd = hash_password(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pwd, role=user.role.upper())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": str(new_user.id), "email": new_user.email, "role": new_user.role}

@app.post("/api/v1/auth/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user: raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(user.password, db_user.hashed_password): raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"user_id": str(db_user.id), "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}

# --- PROFILE ROUTES ---
@app.post("/api/v1/donors/profile")
def create_donor_profile(profile_data: schemas.DonorProfileCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "DONOR": raise HTTPException(status_code=403, detail="Only donors allowed")
    existing = db.query(models.DonorProfile).filter(models.DonorProfile.user_id == current_user.id).first()
    if existing: raise HTTPException(status_code=400, detail="Profile exists")
    new_profile = models.DonorProfile(user_id=current_user.id, blood_group=profile_data.blood_group.upper(), location=profile_data.location, availability=profile_data.availability, last_donation_date=profile_data.last_donation_date)
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return {"message": "Donor profile created", "blood_group": new_profile.blood_group}

@app.post("/api/v1/hospitals/profile")
def create_hospital_profile(profile_data: schemas.HospitalProfileCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "HOSPITAL": raise HTTPException(status_code=403, detail="Only hospitals allowed")
    existing = db.query(models.HospitalProfile).filter(models.HospitalProfile.user_id == current_user.id).first()
    if existing: raise HTTPException(status_code=400, detail="Profile exists")
    new_profile = models.HospitalProfile(user_id=current_user.id, hospital_name=profile_data.hospital_name, address=profile_data.address)
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return {"message": "Hospital profile created", "name": new_profile.hospital_name}

@app.post("/api/v1/bloodbanks/profile")
def create_bloodbank_profile(profile_data: schemas.BloodBankProfileCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "BLOOD_BANK": raise HTTPException(status_code=403, detail="Only blood banks allowed")
    existing = db.query(models.BloodBankProfile).filter(models.BloodBankProfile.user_id == current_user.id).first()
    if existing: raise HTTPException(status_code=400, detail="Profile exists")
    new_profile = models.BloodBankProfile(user_id=current_user.id, bank_name=profile_data.bank_name, address=profile_data.address)
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return {"message": "Blood Bank profile created", "name": new_profile.bank_name}

# --- INVENTORY ROUTE ---
@app.post("/api/v1/inventory/update")
def update_inventory(inv_data: schemas.InventoryUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "BLOOD_BANK": raise HTTPException(status_code=403, detail="Only blood banks can update inventory")
    existing_inv = db.query(models.BloodInventory).filter(
        models.BloodInventory.bank_id == current_user.id,
        models.BloodInventory.blood_group == inv_data.blood_group.upper()
    ).first()

    if existing_inv:
        existing_inv.units_available = inv_data.units
        existing_inv.last_updated = datetime.utcnow()
        db.commit()
        return {"message": "Inventory updated", "blood_group": existing_inv.blood_group, "new_total": existing_inv.units_available}
    else:
        new_inv = models.BloodInventory(bank_id=current_user.id, blood_group=inv_data.blood_group.upper(), units_available=inv_data.units)
        db.add(new_inv)
        db.commit()
        return {"message": "Inventory created", "blood_group": new_inv.blood_group, "total": new_inv.units_available}

# --- AI NATURAL LANGUAGE PARSER (UPDATED FOR GROQ) ---
@app.post("/api/v1/requests/parse")
def parse_natural_request(request_data: schemas.NaturalLanguageRequest):
    """
    Takes messy doctor notes and uses Groq LLM to extract structured data.
    """
    prompt = f"""
    A doctor is requesting blood. Extract the following information from this text: 
    '{request_data.text}'
    
    Return the result as a JSON object with these keys:
    - "blood_group" (string, e.g., "O+", "A-")
    - "units_required" (integer)
    - "urgency" (string, either "HIGH" or "NORMAL")
    
    If you cannot find a value, use null.
    """

    try:
        # CALLING GROQ INSTEAD OF OPENAI
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192", # Groq's fast Llama3 model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0 
        )
        
        ai_response_text = response.choices[0].message.content
        return {"ai_parsed_data": ai_response_text, "original_text": request_data.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Parsing failed: {str(e)}")

# --- BLOOD REQUEST & MATCHING LOGIC ---
@app.post("/api/v1/requests", response_model=schemas.RequestResponse)
def create_blood_request(req_data: schemas.RequestCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "HOSPITAL": raise HTTPException(status_code=403, detail="Only hospitals can request blood")

    new_request = models.BloodRequest(
        hospital_id=current_user.id,
        blood_group=req_data.blood_group.upper(),
        units_required=req_data.units_required,
        urgency=req_data.urgency.upper(),
        location=req_data.location
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    three_months_ago = datetime.utcnow() - timedelta(days=90)
    
    matched_donors = db.query(models.DonorProfile).filter(
        models.DonorProfile.blood_group == new_request.blood_group,
        models.DonorProfile.availability == True,
        (models.DonorProfile.last_donation_date == None) | (models.DonorProfile.last_donation_date <= three_months_ago)
    ).all()

    matched_list = []
    for donor in matched_donors:
        matched_list.append(schemas.MatchedDonor(
            donor_id=str(donor.user_id),
            blood_group=donor.blood_group,
            location=donor.location,
            last_donation=donor.last_donation_date
        ))

    return schemas.RequestResponse(
        request_id=str(new_request.id),
        status="MATCHED" if matched_list else "PENDING",
        matched_donors=matched_list
    )