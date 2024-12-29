import os
import pika
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

def get_rabbitmq_connection():
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()
    channel.queue_declare(queue='cart_queue')
    return connection, channel

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
    connection, channel = get_rabbitmq_connection()
    message = {"action": "add", "user_id": user_id, "product_id": requested_product_id}
    channel.basic_publish(exchange='', routing_key='cart_queue', body=str(message))
    connection.close()
    return {"message": "Product add request sent"}

@app.delete("/cart/{user_id}/remove_product")
def remove_product_from_cart(user_id: int, requested_product_id: int, db: Session = Depends(get_db)):
    connection, channel = get_rabbitmq_connection()
    message = {"action": "remove", "user_id": user_id, "product_id": requested_product_id}
    channel.basic_publish(exchange='', routing_key='cart_queue', body=str(message))
    connection.close()
    return {"message": "Product remove request sent"}
