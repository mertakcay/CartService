from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import SessionLocal, Cart

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Cart Service"}

@app.get("/cart")
def read_cart(db: Session = Depends(get_db)):
    carts = db.query(Cart).all()
    return {"carts": carts}

@app.get("/cart/{user_id}")
def read_cart_by_user(user_id: int, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return {"cart": cart}

@app.post("/cart/{user_id}/add_product")
def add_product_to_cart(user_id: int, requested_product_id: int, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id, product_ids=[requested_product_id])
        db.add(cart)
        db.commit()
    else:
        cart.product_ids.append(requested_product_id)
        db.commit()
    
    return {"message": "Product added to cart", "cart": cart}

@app.delete("/cart/{user_id}/remove_product")
def remove_product_from_cart(user_id: int, requested_product_id: int, db: Session = Depends(get_db)):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart.product_ids.remove(requested_product_id)
    db.commit()
    
    return {"message": "Product removed from cart", "cart": cart}
