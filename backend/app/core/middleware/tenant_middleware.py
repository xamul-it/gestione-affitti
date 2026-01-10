"""
Middleware to set tenant context based on JWT token.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.auth.security import decode_token


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to set PostgreSQL search_path based on tenant in JWT token.

    Extracts tenant_schema from JWT and stores it in request.state.
    The get_db() dependency reads this value and sets search_path automatically.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process each request and set tenant context if present.

        Args:
            request: The incoming request
            call_next: The next middleware/endpoint in chain

        Returns:
            Response from the next handler
        """
        # Extract token from Authorization header
        authorization = request.headers.get("Authorization")

        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")

            # Decode token to get tenant_schema
            payload = decode_token(token)
            if payload:
                tenant_schema = payload.get("tenant_schema")

                if tenant_schema:
                    # Validate schema name (security)
                    if tenant_schema.replace('_', '').replace('-', '').isalnum():
                        # Store tenant_schema in request.state
                        # get_db() dependency will read this and set search_path
                        request.state.tenant_schema = tenant_schema
                    else:
                        print(f"⚠️  Invalid tenant schema name: {tenant_schema}")

        # Continue with request processing
        response = await call_next(request)
        return response
