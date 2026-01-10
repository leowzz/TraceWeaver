import uuid

import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core import security
from app.core.config import settings
from app.core.context import CtxInfo, _ctx_var
from app.models import TokenPayload


class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        user_id = self._extract_user_id(request)
        trace_id = uuid.uuid4().hex[-8:]

        # Initialize context for the request
        token = _ctx_var.set(CtxInfo(user_id=user_id, trace_id=trace_id))
        try:
            response = await call_next(request)
            return response
        finally:
            _ctx_var.reset(token)

    def _extract_user_id(self, request: Request) -> str | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(
                token, settings.app.secret_key, algorithms=[security.ALGORITHM]
            )
            token_data = TokenPayload(**payload)
            return token_data.sub
        except Exception:
            # Token validation fails, or payload is invalid.
            # We don't raise here, as some routes might be public.
            # Authentication is still handled by dependencies like get_current_user.
            return None
