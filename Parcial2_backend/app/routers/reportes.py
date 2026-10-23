from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from fastapi.responses import Response
from app.database import get_db
from app.services.auth_service import get_current_user
from app.schemas.reports import ReportFilters,ReportPrompt
from app.services import reports

router=APIRouter(prefix='/reportes',tags=['Reportes'])
@router.get('/tipos')
def types(_=Depends(get_current_user),cur=Depends(get_db)):
    reports.access(cur);return reports.TITLES
@router.post('/convencional')
def conventional(data:ReportFilters,_=Depends(get_current_user),cur=Depends(get_db)):
    return reports.execute(cur,data)
@router.post('/generativo')
def generative(data:ReportPrompt,_=Depends(get_current_user),cur=Depends(get_db)):
    intent=reports.interpret(cur,data.texto)
    return {'intencion':intent.model_dump(mode='json'),'reporte':reports.execute(cur,intent.filtros) if intent.estado=='listo' else None}
@router.get('/{identifier}')
def result(identifier:UUID,_=Depends(get_current_user),cur=Depends(get_db)):
    return reports.saved(cur,identifier)
@router.get('/{identifier}/exportar/{format}')
def export(identifier:UUID,format:str,_=Depends(get_current_user),cur=Depends(get_db)):
    result=reports.saved(cur,identifier)
    if format not in {'pdf','xlsx'}:raise HTTPException(422,'Formato disponible: pdf o xlsx.')
    data=reports.pdf(result) if format=='pdf' else reports.xlsx(result)
    media='application/pdf' if format=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return Response(data,media_type=media,headers={'Content-Disposition':f'attachment; filename="reporte-{identifier}.{format}"','Cache-Control':'no-store'})
