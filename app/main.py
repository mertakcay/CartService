import os
import json
import pika
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .models import SessionLocal, CartDB, CartSchema, ProductSchema

app = FastAPI(title="Cart Service", version="1.0.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RabbitMQClient:
    def __init__(self):
        self.url = os.getenv("RABBITMQ_URL")
        
    def get_connection(self):
        connection = pika.BlockingConnection(pika.URLParameters(self.url))
        channel = connection.channel()
        channel.queue_declare(queue='cart_queue')
        return connection, channel

    def publish_message(self, message: dict):
        connection, channel = self.get_connection()
        try:
            channel.basic_publish(
                exchange='',
                routing_key='cart_queue',
                body=json.dumps(message)
            )
        finally:
            connection.close()

rabbitmq_client = RabbitMQClient()

@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    return {"message": "Welcome to the Cart Service"}

@app.get("/cart", response_model=List[CartSchema], status_code=status.HTTP_200_OK)
def read_carts(db: Session = Depends(get_db)):
    carts = db.query(CartDB).all()
    return [
        CartSchema(
            id=cart.id,
            user_id=cart.user_id,
            products=[
                ProductSchema(id=pid, amount=amt)
                for pid, amt in zip(cart.product_ids, cart.amounts)
            ]
        ) for cart in carts
    ]

@app.get("/cart/{user_id}", response_model=CartSchema, status_code=status.HTTP_200_OK)
def read_cart_by_user(user_id: int, db: Session = Depends(get_db)):
    cart = db.query(CartDB).filter(CartDB.user_id == user_id).first()
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart not found for user {user_id}"
        )
    return CartSchema(
        id=cart.id,
        user_id=cart.user_id,
        products=[
            ProductSchema(id=pid, amount=amt)
            for pid, amt in zip(cart.product_ids, cart.amounts)
        ]
    )

@app.post("/cart/{user_id}/add_product", status_code=status.HTTP_202_ACCEPTED)
def add_product_to_cart(
    user_id: int,
    product: ProductSchema,
    db: Session = Depends(get_db)
):
    try:
        message = {
            "action": "add",
            "user_id": user_id,
            "product_id": product.id,
            "amount": product.amount
        }
        rabbitmq_client.publish_message(message)
        return {"message": "Product add request sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {str(e)}"
        )

@app.delete("/cart/{user_id}/remove_product", status_code=status.HTTP_202_ACCEPTED)
def remove_product_from_cart(
    user_id: int,
    product: ProductSchema,
    db: Session = Depends(get_db)
):
    try:
        message = {
            "action": "remove",
            "user_id": user_id,
            "product_id": product.id,
            "amount": product.amount
        }
        rabbitmq_client.publish_message(message)
        return {"message": "Product remove request sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {str(e)}"
        )

@app.delete("/cart/{user_id}", status_code=status.HTTP_202_ACCEPTED)
def delete_cart(user_id: int, db: Session = Depends(get_db)):
    try:
        message = {
            "action": "delete_cart",
            "user_id": user_id,
            "product_id": None,
            "amount": None
        }
        rabbitmq_client.publish_message(message)
        return {"message": f"Cart deletion request for user {user_id} sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {str(e)}"
        )
