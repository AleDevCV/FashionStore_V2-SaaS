"""Contexto por petición, compartido por todas las conexiones y servicios."""
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class TenantContext:
    tenant_id: int
    user_id: Optional[int] = None
    role: str = ''
    email: str = ''
    platform: bool = False
    slug: str = ''
    account_id: Optional[int] = None

context: ContextVar[Optional[TenantContext]] = ContextVar('tenant_context', default=None)

def require_context() -> TenantContext:
    value=context.get()
    if value is None:
        from fastapi import HTTPException
        raise HTTPException(400,'Seleccione una empresa antes de continuar.')
    return value

def authenticated_context() -> TenantContext:
    value=require_context()
    if value.user_id is None:
        from fastapi import HTTPException
        raise HTTPException(401,'Debe iniciar sesión para esta operación.')
    return value
