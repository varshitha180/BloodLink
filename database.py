from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- CHANGE THESE TO YOUR POSTGRES DETAILS ---
DB_USER = "postgres"
DB_PASSWORD = "24r11a05by" # <-- Put your postgres password here
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "bloodlink_db" # <-- Make sure you created this database in pgAdmin

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()