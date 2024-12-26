# Cart Service

This project is a microservice for managing a shopping cart, developed with Python FastAPI. It uses PostgreSQL for the database and RabbitMQ for handling asynchronous tasks such as adding and removing products from the cart.

## Folder Structure

```
CartService/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── consumer.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

- `app/`: Contains the FastAPI application code.
  - `main.py`: The main FastAPI application file with endpoints.
  - `models.py`: The SQLAlchemy models for the database.
  - `consumer.py`: The RabbitMQ consumer for handling add/remove product tasks.
- `Dockerfile`: Dockerfile for building the FastAPI application container.
- `docker-compose.yml`: Docker Compose file for setting up the application, PostgreSQL, and RabbitMQ services.
- `requirements.txt`: List of Python dependencies.
- `README.md`: This file.

## Setup and Running

### Prerequisites

- Docker
- Docker Compose

### Steps

1. **Build the Docker images:**

   ```sh
   docker-compose build
   ```

2. **Start the Docker containers:**

   ```sh
   docker-compose up
   ```

3. **Run the RabbitMQ consumer:**

   In a separate terminal, run the following command to start the RabbitMQ consumer:

   ```sh
   docker-compose exec cart-service python app/consumer.py
   ```

### Endpoints

- `GET /`: Welcome message.
- `GET /cart`: Retrieve all carts.
- `GET /cart/{user_id}`: Retrieve the cart for a specific user.
- `POST /cart/{user_id}/add_product`: Add a product to the cart for a specific user.
- `DELETE /cart/{user_id}/remove_product`: Remove a product from the cart for a specific user.

### Environment Variables

- `DATABASE_URL`: The URL for the PostgreSQL database.
- `RABBITMQ_URL`: The URL for the RabbitMQ server.

### Dependencies

- `fastapi`: Web framework for building APIs with Python.
- `uvicorn`: ASGI server for serving FastAPI applications.
- `sqlalchemy`: SQL toolkit and ORM for Python.
- `asyncpg`: PostgreSQL database adapter for Python.
- `databases`: Async database support for SQLAlchemy.
- `pika`: RabbitMQ client library for Python.

## License

This project is licensed under the MIT License.
