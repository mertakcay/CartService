import os
import pika
import json
from sqlalchemy.orm import Session
from .models import SessionLocal, Cart

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def callback(ch, method, properties, body):
    message = json.loads(body)
    action = message.get("action")
    user_id = message.get("user_id")
    product_id = message.get("product_id")

    db = next(get_db())
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if action == "add":
        if not cart:
            cart = Cart(user_id=user_id, product_ids=[product_id])
            db.add(cart)
        else:
            cart.product_ids.append(product_id)
        db.commit()
    elif action == "remove":
        if cart and product_id in cart.product_ids:
            cart.product_ids.remove(product_id)
            db.commit()

rabbitmq_url = os.getenv("RABBITMQ_URL")
connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
channel = connection.channel()
channel.queue_declare(queue='cart_queue')
channel.basic_consume(queue='cart_queue', on_message_callback=callback, auto_ack=True)

print('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
