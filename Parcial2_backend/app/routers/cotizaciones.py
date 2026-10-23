from fastapi import APIRouter,Depends
from pydantic import BaseModel,Field
from app.database import get_db
from app.services.auth_service import get_current_user
from app.services.commerce import quote,authorized_branch
router=APIRouter(prefix='/ventas',tags=['Cotización comercial'])
class Line(BaseModel):
    id_variante_prenda:int=Field(gt=0)
    cantidad:int=Field(gt=0,le=10000)
class Quote(BaseModel):
    id_sucursal:int=Field(gt=0)
    items:list[Line]=Field(min_length=1,max_length=100)
@router.post('/cotizar')
def quotation(data:Quote,_=Depends(get_current_user),cur=Depends(get_db)):
    authorized_branch(cur,data.id_sucursal,allow_customer=True)
    lines=quote(cur,[x.model_dump() for x in data.items],data.id_sucursal)
    return {'items':lines,'total':sum(x['subtotal'] for x in lines)}
