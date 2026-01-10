import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from pydantic import BaseModel


class CtxInfo(BaseModel):
    user_id: uuid.UUID | None = None
    trace_id: str | None = None


_ctx_var: ContextVar[CtxInfo | None] = ContextVar("ctx", default=None)


class CtxProxy:
    def __getattr__(self, name: str) -> Any:
        info = _ctx_var.get()
        if info is None:
            return None
        return getattr(info, name)

    def __setattr__(self, name: str, value: Any) -> None:
        info = _ctx_var.get()
        if info is None:
            raise RuntimeError("Context not initialized.")
        setattr(info, name, value)


ctx: CtxInfo = CtxProxy()  # type: ignore


@contextmanager
def mock_ctx(user_id: str | None = "mock_user"):
    token = _ctx_var.set(CtxInfo(user_id=user_id, trace_id=uuid.uuid4().hex[-8:]))
    try:
        yield
    finally:
        _ctx_var.reset(token)
