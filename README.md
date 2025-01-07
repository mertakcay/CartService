# Cart Service

A microservice-based shopping cart system built with FastAPI, PostgreSQL, and RabbitMQ.

## Features

- Asynchronous cart operations using message queues
- RESTful API endpoints for cart management
- Persistent storage with PostgreSQL
- Containerized with Docker
- Scalable consumer architecture
- Robust error handling and logging

## Architecture

The service consists of two main components:
1. **API Service**: Handles HTTP requests and publishes messages to RabbitMQ
2. **Consumer Service**: Processes cart operations asynchronously

### Tech Stack

- **FastAPI**: Web framework for building APIs
- **PostgreSQL**: Primary database
- **RabbitMQ**: Message queue for async operations
- **SQLAlchemy**: ORM for database operations
- **Docker**: Containerization
- **Pydantic**: Data validation

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Environment Variables

Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://postgres:password@db/postgres
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=postgres
RABBITMQ_DEFAULT_USER=guest
RABBITMQ_DEFAULT_PASS=guest
```

## Running the Service

### Using Docker Compose (Recommended)

1. Make sure Docker and Docker Compose are installed
2. Run the services:
```bash
docker-compose up --build
```

This will start:
- The FastAPI application
- PostgreSQL database
- RabbitMQ message broker
- Cart consumer service

### Manual Setup

1. Start PostgreSQL and create a database
2. Start RabbitMQ server
3. Update the `.env` file with your local connection details
4. Run the FastAPI application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
5. In a separate terminal, run the consumer:
```bash
python -m app.consumer
```

## API Endpoints

### GET /
- Welcome message
- Response: `{"message": "Welcome to the Cart Service"}`

### GET /cart
- List all carts
- Response: List of cart objects

### GET /cart/{user_id}
- Get cart for specific user
- Response: Cart object for the specified user

### POST /cart/{user_id}/add_product
- Add product to user's cart
- Request body:
```json
{
    "id": "product_id",
    "amount": "quantity"
}
```

### DELETE /cart/{user_id}/remove_product
- Remove product from user's cart
- Request body:
```json
{
    "id": "product_id",
    "amount": "quantity"
}
```

### DELETE /cart/{user_id}
- Delete entire cart for a specific user
- Response: 
```json
{
    "message": "Cart deletion request for user {user_id} sent successfully"
}
```
- Status Codes:
  - 202: Accepted (deletion request processed)
  - 500: Internal Server Error

## Error Handling

The service includes comprehensive error handling:
- 404: Resource not found
- 500: Internal server error
- Input validation errors
- Database connection errors
- Message broker connection errors

## Monitoring

The service includes logging for monitoring:
- Application logs
- Consumer logs
- Database operations
- Message processing

### Logging Example 
#### Add Product

```json
{
cartservice-consumer-1  | INFO:__main__:Received message: b'{"action": "add", "user_id": 1, "product_id": 3, "amount": 1}'
cartservice-consumer-1  | INFO:__main__:Parsed message: {'action': 'add', 'user_id': 1, 'product_id': 3, 'amount': 1}
cartservice-consumer-1  | INFO:__main__:Validated message data - Action: add, User: 1, Product: 3, Amount: 1
cartservice-consumer-1  | INFO:__main__:Processing add action
cartservice-consumer-1  | INFO:__main__:Processing add product request - User: 1, Product: 3, Amount: 1
}
```


#### Remove Product
```json
{
cartservice-api-1       | INFO:     192.168.240.1:65080 - "DELETE /cart/1/remove_product HTTP/1.1" 202 Accepted
cartservice-rabbitmq-1  | 2025-01-07 15:46:06.704015+00:00 [info] <0.1147.0> closing AMQP connection <0.1147.0> (192.168.240.4:43468 -> 192.168.240.3:5672, vhost: '/', user: 'guest')
cartservice-consumer-1  | INFO:__main__:Current cart state - Products: [2, 3], Amounts: [3, 4]
cartservice-consumer-1  | INFO:__main__:Found product in cart - Index: 1, Current amount: 4
cartservice-consumer-1  | INFO:__main__:Decreased amount - Product: 3, Old: 4, New: 2
cartservice-consumer-1  | INFO:__main__:Updated cart state - Products: [2, 3], Amounts: [3, 2]
cartservice-consumer-1  | INFO:__main__:Successfully committed changes - User: 1, Final cart state: {'_sa_instance_state': <sqlalchemy.orm.state.InstanceState object at 0xfffface28970>}
cartservice-api-1       | INFO:     192.168.240.1:60586 - "GET /cart/1 HTTP/1.1" 200 OK
}
```

#### Delete Cart
```json
{
cartservice-consumer-1  | INFO:__main__:Processing delete cart request for user: 1
cartservice-consumer-1  | INFO:__main__:Successfully deleted cart for user: 1
cartservice-api-1       | INFO:     192.168.240.1:65080 - "DELETE /cart/1 HTTP/1.1" 202 Accepted
}
```

## Development

To contribute to the project:
1. Create a new branch
2. Make your changes
3. Write/update tests
4. Submit a pull request



## License

[MIT License](LICENSE) 