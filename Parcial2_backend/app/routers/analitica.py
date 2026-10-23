from fastapi import APIRouter,Depends,Query
from app.database import get_db
from app.services.auth_service import get_current_user
from app.services import analytics
router=APIRouter(prefix='/analitica',tags=['Machine Learning'])
@router.get('/modelos')
def models(_=Depends(get_current_user),cur=Depends(get_db)):
    analytics.access(cur);return analytics.metadata()
@router.get('/dashboard')
def dashboard(sucursal:int|None=Query(default=None,gt=0),_=Depends(get_current_user),cur=Depends(get_db)):
    return analytics.dashboard(cur,sucursal)
