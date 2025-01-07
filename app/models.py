from typing import List, Optional
import os
from sqlalchemy import create_engine, Column, Integer, String, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tenacity import retry, wait_fixed, stop_after_attempt
from pydantic import BaseModel

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")

@retry(wait=wait_fixed(2), stop=stop_after_attempt(10))
def get_engine():
    return create_engine(DATABASE_URL)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Models
class CartDB(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    product_ids = Column(ARRAY(Integer))
    amounts = Column(ARRAY(Integer))

# Pydantic Models
class ProductSchema(BaseModel):
    id: int
    amount: int

class CartSchema(BaseModel):
    id: Optional[int]
    user_id: int
    products: List[ProductSchema]

    class Config:
        orm_mode = True

# Create tables
Base.metadata.create_all(bind=engine)
