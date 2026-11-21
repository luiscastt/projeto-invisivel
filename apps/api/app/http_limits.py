from starlette.responses import JSONResponse


class RequestSizeLimit:
    """Bound actual request bytes before multipart parsing/spooling, including chunked bodies."""
    def __init__(self, app, max_bytes=6 * 1024 * 1024):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Tamanho de requisição inválido."}, status_code=400)(scope, receive, send)
        if length > self.max_bytes:
            return await JSONResponse({"detail": "Requisição excede o limite de 6 MiB."}, status_code=413)(scope, receive, send)
        data = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            data.extend(message.get("body", b""))
            if len(data) > self.max_bytes:
                return await JSONResponse({"detail": "Requisição excede o limite de 6 MiB."}, status_code=413)(scope, receive, send)
            if not message.get("more_body", False):
                break
        sent = False
        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": bytes(data), "more_body": False}
            return await receive()
        await self.app(scope, replay, send)
