from pydantic import BaseModel

# Define the Product model
class Product(BaseModel):
    name: str
    amount: int

# Define the Cart model
class Cart(BaseModel):
    cart_id: str
    products: list
