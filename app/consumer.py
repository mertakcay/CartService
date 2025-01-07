import os
import pika
import json
import logging
from sqlalchemy.orm import Session
from contextlib import contextmanager
from .models import SessionLocal, CartDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class CartConsumer:
    def __init__(self):
        self.rabbitmq_url = os.getenv("RABBITMQ_URL")
        
    def process_add_product(self, db: Session, user_id: int, product_id: int, amount: int):
        cart = db.query(CartDB).filter(CartDB.user_id == user_id).first()
        if not cart:
            cart = CartDB(user_id=user_id, product_ids=[product_id], amounts=[amount])
            db.add(cart)
        else:
            if product_id in cart.product_ids:
                index = cart.product_ids.index(product_id)
                cart.amounts[index] += amount
            else:
                cart.product_ids.append(product_id)
                cart.amounts.append(amount)
        db.commit()
        logger.info(f"Added product {product_id} with amount {amount} to cart for user {user_id}")

    def process_remove_product(self, db: Session, user_id: int, product_id: int, amount: int):
        cart = db.query(CartDB).filter(CartDB.user_id == user_id).first()
        if cart and product_id in cart.product_ids:
            index = cart.product_ids.index(product_id)
            if cart.amounts[index] <= amount:
                cart.product_ids.pop(index)
                cart.amounts.pop(index)
            else:
                cart.amounts[index] -= amount
            db.commit()
            logger.info(f"Removed product {product_id} with amount {amount} from cart for user {user_id}")
        else:
            logger.warning(f"Cart not found or product {product_id} not in cart for user {user_id}")

    def process_delete_cart(self, db: Session, user_id: int):
        logger.info(f"Processing delete cart request for user: {user_id}")
        try:
            cart = db.query(CartDB).filter(CartDB.user_id == user_id).first()
            if cart:
                db.delete(cart)
                db.commit()
                logger.info(f"Successfully deleted cart for user: {user_id}")
            else:
                logger.warning(f"Cart not found for user: {user_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting cart for user {user_id}: {str(e)}")
            raise

    def callback(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            action = message.get("action")
            user_id = message.get("user_id")
            product_id = message.get("product_id")
            amount = message.get("amount")

            if not action or not user_id:
                logger.error(f"Invalid message format: {message}")
                return

            with get_db() as db:
                if action == "add":
                    if not all([product_id, amount]):
                        logger.error("Missing product_id or amount for add action")
                        return
                    self.process_add_product(db, user_id, product_id, amount)
                elif action == "remove":
                    if not all([product_id, amount]):
                        logger.error("Missing product_id or amount for remove action")
                        return
                    self.process_remove_product(db, user_id, product_id, amount)
                elif action == "delete_cart":
                    self.process_delete_cart(db, user_id)
                else:
                    logger.error(f"Unknown action: {action}")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode message: {body}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    def run(self):
        try:
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()
            channel.queue_declare(queue='cart_queue')
            channel.basic_consume(
                queue='cart_queue',
                on_message_callback=self.callback,
                auto_ack=True
            )

            logger.info('Cart consumer started. Waiting for messages...')
            channel.start_consuming()

        except Exception as e:
            logger.error(f"Failed to start consumer: {str(e)}")
            raise

if __name__ == "__main__":
    consumer = CartConsumer()
    consumer.run()
