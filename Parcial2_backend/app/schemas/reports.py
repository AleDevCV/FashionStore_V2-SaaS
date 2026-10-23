from datetime import date,timedelta
from typing import Literal
from pydantic import BaseModel,Field,ConfigDict,model_validator

ReportType=Literal['ventas_sucursal','productos_vendidos','evolucion_ventas','stock_bajo','ingresos_categoria','comparacion_sucursales']
class ReportFilters(BaseModel):
    model_config=ConfigDict(extra='forbid')
    tipo:ReportType
    desde:date=Field(default_factory=lambda:date.today()-timedelta(days=30))
    hasta:date=Field(default_factory=date.today)
    sucursal:int|None=Field(default=None,gt=0)
    categoria:int|None=Field(default=None,gt=0)
    agrupacion:Literal['dia','semana','mes']='dia'
    umbral:int=Field(default=5,ge=0,le=10000)
    limite:int=Field(default=100,ge=1,le=500)
    @model_validator(mode='after')
    def period(self):
        if self.hasta<self.desde or (self.hasta-self.desde).days>365:raise ValueError('El período debe estar ordenado y abarcar como máximo 366 días.')
        return self
class ReportPrompt(BaseModel):
    texto:str=Field(min_length=5,max_length=2000)
class ReportIntent(BaseModel):
    model_config=ConfigDict(extra='forbid')
    estado:Literal['listo','aclarar','no_soportado']
    mensaje:str=Field(max_length=500)
    filtros:ReportFilters|None=None
