from starlette.types import ASGIApp, Receive, Scope, Send


class SecurityHeadersMiddleware:
    """ASGI middleware to add common security headers to every response.

    This is intentionally simple and synchronous-friendly. You can extend or
    replace it with more advanced logic if needed (e.g., per-route CSP).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            # Only intercept http.response.start to add headers
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))

                # Security headers
                security_headers = {
                    b"Strict-Transport-Security": b"max-age=63072000; includeSubDomains; preload",
                    b"X-Frame-Options": b"DENY",
                    b"X-Content-Type-Options": b"nosniff",
                    b"Referrer-Policy": b"no-referrer",
                    b"Permissions-Policy": b"geolocation=()",
                    # CSP that allows FastAPI docs to work (Swagger UI and ReDoc)
                    b"Content-Security-Policy": b"default-src 'self'; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://cdn.jsdelivr.net https://fastapi.tiangolo.com; connect-src 'self' https://cdn.jsdelivr.net",
                }

                # Merge/append headers (preferring existing headers if present)
                new_headers = list(message.get("headers", []))
                for k, v in security_headers.items():
                    if k not in headers:
                        new_headers.append((k, v))

                message["headers"] = new_headers

            await send(message)

        await self.app(scope, receive, send_wrapper)
