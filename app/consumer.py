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
        # Get or create cart for user
        cart = db.query(CartDB).filter(CartDB.user_id == user_id).first()
        logger.info(f"Processing add product - User: {user_id}, Product: {product_id}, Amount: {amount}")
        
        if not cart:
            # Create new cart if it doesn't exist
            cart = CartDB(
                user_id=user_id,
                product_ids=[product_id],
                amounts=[amount]
            )
            db.add(cart)
            logger.info(f"Created new cart for user {user_id} with product {product_id}")
        else:
            # Ensure arrays are initialized and are lists
            cart.product_ids = list(cart.product_ids or [])
            cart.amounts = list(cart.amounts or [])
            
            try:
                if product_id in cart.product_ids:
                    # Update existing product amount
                    index = cart.product_ids.index(product_id)
                    cart.amounts[index] += amount
                    logger.info(f"Updated amount for product {product_id} in cart for user {user_id}")
                else:
                    # Add new product to cart
                    cart.product_ids.append(product_id)
                    cart.amounts.append(amount)
                    logger.info(f"Added new product {product_id} to cart for user {user_id}")
            except Exception as e:
                logger.error(f"Error updating cart: {str(e)}")
                raise

        try:
            db.commit()
            logger.info(f"Successfully saved cart changes - User: {user_id}, Products: {cart.product_ids}, Amounts: {cart.amounts}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to commit changes: {str(e)}")
            raise

    def process_remove_product(self, db: Session, user_id: int, product_id: int, amount: int):
        cart = db.query(CartDB).filter(CartDB.user_id == user_id).first()
        logger.info(f"Processing remove product - User: {user_id}, Product: {product_id}, Amount: {amount}")

        if not cart:
            logger.warning(f"Cart not found for user {user_id}")
            return
            
        if not cart.product_ids or product_id not in cart.product_ids:
            logger.warning(f"Product {product_id} not found in cart for user {user_id}")
            return

        try:
            # Ensure we're working with lists
            cart.product_ids = list(cart.product_ids or [])
            cart.amounts = list(cart.amounts or [])
            
            index = cart.product_ids.index(product_id)
            current_amount = cart.amounts[index]
            
            if amount >= current_amount:
                # Remove the product completely
                cart.product_ids.pop(index)
                cart.amounts.pop(index)
                logger.info(f"Removed product {product_id} completely from cart for user {user_id}")
            else:
                # Decrease the amount
                cart.amounts[index] = current_amount - amount
                logger.info(f"Decreased amount of product {product_id} by {amount} for user {user_id}")

            try:
                db.commit()
                logger.info(f"Successfully saved cart changes - User: {user_id}, Products: {cart.product_ids}, Amounts: {cart.amounts}")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to commit changes: {str(e)}")
                raise

        except Exception as e:
            logger.error(f"Error updating cart: {str(e)}")
            raise

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
