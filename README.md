# Auth Service

Authentication and Authorization Service

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
python manage.py createsuperuser
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Documentation
* http://127.0.0.1/api/auth/openapi (Swagger)
* http://127.0.0.1/api/auth/openapi.json (openapi)

## Description of Additional Service Methods

### Running functional-tests
Installing dependencies from requirements-dev.txt at the project root

```commandline
pytest -vv auth_service
```

### Running linters
Installing dependencies from requirements-dev.txt at the project root

```commandline
isort auth_service
flake8 auth_service
black --skip-string-normalization auth_service
```

### Description of ENV Variables

| Variable Name            | Possible Value                                      | Description                                                             |
|:-------------------------|-----------------------------------------------------|:------------------------------------------------------------------------|
| DEBUG                    | False                                               | Debug mode                                                              |
| PROJECT_NAME             | Auth                                                | Name of the service (displayed in Swagger)                              |
| REDIS_HOST               | redis                                               | Redis server hostname                                                   |
| REDIS_PORT               | 6379                                                | Redis server port                                                       |
| PG_DSN                   | postgresql+asyncpg://app:123qwe@localhost:5433/auth | PostgreSQL database DSN (Data Source Name)                              |
| SECRET_KEY               | secret                                              | Secret key                                                              |
| JAEGER_TRACE             | True                                                | Enable Jaeger tracing                                                   |
| JAEGER_AGENT_HOST        | localhost                                           | Jaeger agent host                                                       |
| JAEGER_AGENT_PORT        | 6831                                                | Jaeger agent port                                                       |
| REQUEST_LIMIT_PER_MINUTE | 20                                                  | Request rate limit (per minute). If set to 0, rate limiting is disabled |
| GOOGLE_REDIRECT_URI      | http://localhost/api/v1/google/auth_return          | Google authentication redirect URI                                      |
| GOOGLE_CLIENT_ID         | 6anqlc8.apps.googleusercontent.com                  | Google authentication client ID                                         |
| GOOGLE_CLIENT_SECRET     | AAAAAA-sdsdsd-v-wiO2kwkWVIQ9JmsS62Y                 | Google authentication client secret                                     |

### Creating a Superuser
A superuser is created automatically with the login admin@example.com and the password admin.
