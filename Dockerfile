FROM python:3.11.1

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \

    APP_PATH='/opt/app'

WORKDIR $APP_PATH

COPY ./requirements.txt .

RUN  pip install --upgrade pip && pip install  --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT python manage.py migrate && \
           python manage.py createsuperuser && \
           gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
