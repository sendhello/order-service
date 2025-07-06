# Order Service

Order management service for courier delivery

* **Application Language:** Python 3.13
* **Supported Communication Protocols:** REST API
* **Infrastructure Dependencies:** Postgres, Redis
* **System Package Dependencies:** None
* **PostgreSQL Extension Dependencies:** None
* **Environment Role:** development
* **Minimum System Requirements:** 1 CPU, 1Gb RAM

## Service support

Software engineers:

* Ivan Bazhenov (*[@sendhello](https://github.com/sendhello)*)

## Description of Required Methods to Run the Service

### Service Startup
```commandline
on the root
docker compose up --build
```

Or if you want to run it in development mode:

```commandline
# Create a .env.local file with the necessary environment variables
export $(cat .env.local | xargs)
docker compose -f docker-compose-dev.yml up
python manage.py migrate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Documentation
* http://127.0.0.1/api/orders/openapi (Swagger)
* http://127.0.0.1/api/orders/openapi.json (openapi)

## API Endpoints

### Order Management
* `POST /api/v1/orders/` - Create order
* `GET /api/v1/orders/` - Get list of orders (with pagination and filtering)
* `GET /api/v1/orders/{order_id}` - Get order by ID
* `GET /api/v1/orders/tracking/{tracking_id}` - Get order by tracking ID
* `PUT /api/v1/orders/{order_id}` - Update order
* `DELETE /api/v1/orders/{order_id}` - Delete order

### Delivery Management
* `POST /api/v1/orders/{order_id}/assign` - Assign courier
* `POST /api/v1/orders/{order_id}/start` - Start delivery
* `POST /api/v1/orders/{order_id}/complete` - Complete delivery
* `POST /api/v1/orders/{order_id}/cancel` - Cancel order

## Description of Additional Service Methods

### Running functional-tests
Installing dependencies from pyproject.toml at the project root

```commandline
pytest -vv
```

### Running linters
Installing dependencies from pyproject.toml at the project root

```commandline
isort .
flake8 .
black --skip-string-normalization .
```

### Description of ENV Variables

| Variable Name            | Possible Value                                        | Description                                                             |
|:-------------------------|-------------------------------------------------------|:------------------------------------------------------------------------|
| DEBUG                    | False                                                 | Debug mode                                                              |
| PROJECT_NAME             | Order Service                                         | Name of the service (displayed in Swagger)                              |
| REDIS_HOST               | redis                                                 | Redis server hostname                                                   |
| REDIS_PORT               | 6379                                                  | Redis server port                                                       |
| PG_DSN                   | postgresql+asyncpg://app:123qwe@localhost:5433/orders | PostgreSQL database DSN (Data Source Name)                              |
| SECRET_KEY               | secret                                                | JWT secret key for authentication                                       |
| JAEGER_TRACE             | True                                                  | Enable Jaeger tracing                                                   |
| JAEGER_AGENT_HOST        | localhost                                             | Jaeger agent host                                                       |
| JAEGER_AGENT_PORT        | 6831                                                  | Jaeger agent port                                                       |
| REQUEST_LIMIT_PER_MINUTE | 20                                                    | Request rate limit (per minute). If set to 0, rate limiting is disabled |

### Authentication
This service uses JWT authentication. All endpoints require a valid JWT token in the Authorization header.
