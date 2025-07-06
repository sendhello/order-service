from datetime import datetime

from core.settings import settings
from db.redis_db import get_redis


async def is_rate_limit_exceeded(token):
    """Проверка лимита запросов.

    Проверяет сколько запросов за текущую минуту сделал пользователь
    и возвращает True при превышении лимита запросов.

    Пользователем считается владелец access-токена

    Если REQUEST_LIMIT_PER_MINUTE равен 0 - лимит запросов не проверяется
    """
    if settings.request_limit == 0:
        return False

    redis = await get_redis()
    now = datetime.now()
    key = f"{token}:{now.minute}"

    pipe = redis.pipeline()
    pipe.incr(key, 1)
    pipe.expire(key, 60)
    result = await pipe.execute()
    request_number = result[0]
    if request_number > settings.request_limit:
        return True

    return False
