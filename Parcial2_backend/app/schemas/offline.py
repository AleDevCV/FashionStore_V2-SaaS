from datetime import datetime,timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID
from pydantic import BaseModel,Field,ConfigDict,field_validator

class LocalLine(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id_variante_prenda:int=Field(gt=0)
    cantidad:int=Field(gt=0,le=10000)
    precio_unitario:Decimal=Field(ge=0,max_digits=10,decimal_places=2)
    @field_validator('precio_unitario')
    @classmethod
    def cents(cls,value):return value.quantize(Decimal('0.01'))
class Operation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    operation_id:UUID
    version:Literal[1]=1
    tenant_id:int=Field(gt=0)
    author_id:int=Field(gt=0)
    branch_id:int=Field(gt=0)
    device_id:UUID
    kind:Literal['venta','reserva']
    occurred_at:datetime
    lease:str=Field(min_length=30,max_length=8192)
    customer_id:int|None=Field(default=None,gt=0)
    cash_received:Decimal|None=Field(default=None,ge=0,max_digits=12,decimal_places=2)
    items:list[LocalLine]=Field(min_length=1,max_length=100)
    original_operation:UUID|None=None
    @field_validator('occurred_at')
    @classmethod
    def aware(cls,value):
        if value.tzinfo is None:raise ValueError('Fecha local con zona horaria requerida.')
        return value.astimezone(timezone.utc)
    @field_validator('cash_received')
    @classmethod
    def cash_cents(cls,value):return value.quantize(Decimal('0.01')) if value is not None else None
class Batch(BaseModel):
    operations:list[dict]=Field(min_length=1,max_length=50)
    supervision_reason:str=Field(default='',max_length=500)
class Resolution(BaseModel):
    motivo:str=Field(min_length=6,max_length=500)
    compensacion:Decimal=Field(ge=0,max_digits=12,decimal_places=2)
