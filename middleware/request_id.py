from fastapi import Request, status
from fastapi.responses import ORJSONResponse


class RequiredRequestIdMiddleware:
    """Middleware для отклонения запросов без X-Request-Id заголовка

    Нужно для гарантирования передачи ID запросов при включенной телеметрии
    """

    async def __call__(self, request: Request, call_next, *args, **kwargs):
        response = await call_next(request)
        print(f"{request.headers=}")
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
        return response


required_request_id = RequiredRequestIdMiddleware()
