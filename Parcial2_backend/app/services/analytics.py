"""Inferencia diferida con artefactos de la versión, consultas siempre bajo RLS."""
import hashlib,json,os
from pathlib import Path
from functools import lru_cache
from datetime import date,timedelta
from fastapi import HTTPException
from app.services.reports import access,branches,serial
from app.ml_features import demand_features

DIRECTORY=Path(os.getenv('ML_ARTIFACT_DIR',str(Path(__file__).resolve().parents[2]/'ml/artifacts/v1')))

def metadata():
    path=DIRECTORY/'metadata.json'
    if not path.exists():raise HTTPException(503,'Los modelos todavía no están entrenados o instalados.')
    return json.loads(path.read_text(encoding='utf-8'))

@lru_cache(maxsize=2)
def artifact(name):
    import joblib,sklearn,numpy as np
    info=metadata();path=DIRECTORY/name
    if info['sklearn']!=sklearn.__version__ or info.get('numpy')!=np.__version__ or info.get('joblib')!=joblib.__version__ or hashlib.sha256(path.read_bytes()).hexdigest()!=info['artifacts'].get(name):raise HTTPException(503,'Versión o integridad del artefacto incompatible. Reentrene con el entorno fijado.')
    return joblib.load(path) # Solo ruta interna empaquetada y hash verificado; nunca uploads.

def dashboard(cur,selected=None):
    access(cur);scope=branches(cur,selected);today=date.today()
    cur.execute("SET LOCAL statement_timeout='8000ms'")
    cur.execute("SELECT count(*)::int AS ventas,count(*) FILTER(WHERE origen_datos='demostracion')::int AS ventas_demostracion,COALESCE(sum(total),0) AS ingresos,COALESCE(avg(total),0) AS ticket_promedio FROM venta WHERE id_sucursal=ANY(%s) AND fecha_venta>=%s",(scope,today-timedelta(days=30)));kpi=dict(cur.fetchone())
    cur.execute('SELECT count(*)::int AS variantes_bajas FROM inventario_catalogo WHERE id_sucursal=ANY(%s) AND stock<=5',(scope,));kpi.update(cur.fetchone())
    cur.execute('SELECT p.id_prenda,p.nombre,p.precio_base,s.id_sucursal,s.nombre AS sucursal FROM prenda p CROSS JOIN sucursal s WHERE s.id_sucursal=ANY(%s) AND p.estado=\'Activo\' ORDER BY p.id_prenda,s.id_sucursal LIMIT 100',(scope,));targets=[dict(r) for r in cur.fetchall()]
    cur.execute('SELECT vp.id_prenda,v.id_sucursal,v.fecha_venta::date AS dia,sum(d.cantidad)::int AS unidades FROM venta v JOIN detalle_venta d USING(id_venta) JOIN variante_prenda vp USING(id_variante_prenda) WHERE v.id_sucursal=ANY(%s) AND v.fecha_venta>=%s AND v.fecha_venta<%s GROUP BY vp.id_prenda,v.id_sucursal,dia',(scope,today-timedelta(days=28),today));series={}
    for r in cur.fetchall():series[(r['id_prenda'],r['id_sucursal'],r['dia'])]=r['unidades']
    cur.execute('SELECT vp.id_prenda,v.id_sucursal,min(v.fecha_venta)::date AS primera FROM venta v JOIN detalle_venta d USING(id_venta) JOIN variante_prenda vp USING(id_variante_prenda) WHERE v.id_sucursal=ANY(%s) GROUP BY vp.id_prenda,v.id_sucursal',(scope,));first={(r['id_prenda'],r['id_sucursal']):r['primera'] for r in cur.fetchall()}
    forecasts=[];features=[];ready=[]
    for row in targets:
        key=(row['id_prenda'],row['id_sucursal']);start=first.get(key)
        value={'producto':row['nombre'],'id_prenda':row['id_prenda'],'sucursal':row['sucursal'],'id_sucursal':row['id_sucursal'],'fecha':today.isoformat(),'prediccion':None,'estado':'Historial menor a 28 días.'}
        forecasts.append(value)
        if start and start<=today-timedelta(days=28):
            history=[series.get((*key,today-timedelta(days=i)),0) for i in range(28,0,-1)];features.append(demand_features(history,today,row['precio_base'],False));ready.append(value)
    status='disponible';info=None
    try:
        info=metadata()
        if ready:
            from threadpoolctl import threadpool_limits
            with threadpool_limits(limits=1):predictions=artifact('demand.joblib')['model'].predict(features)
            for row,pred in zip(ready,predictions):row.update(prediccion=round(max(0,float(pred)),2),estado='Estimación experimental con modelo sintético; oferta no modelada en esta consulta.')
    except HTTPException as exc:status=str(exc.detail)
    cur.execute("SELECT c.id_cliente,c.nombre_completo,(CURRENT_DATE-max(v.fecha_venta)::date)::int AS recencia,count(*)::int AS frecuencia,sum(v.total) AS monetario FROM cliente c JOIN venta v USING(id_cliente) WHERE v.id_sucursal=ANY(%s) AND v.fecha_venta>=CURRENT_DATE-365 AND c.ci<>'MOSTRADOR' GROUP BY c.id_cliente,c.nombre_completo ORDER BY c.id_cliente LIMIT 500",(scope,));customers=[dict(r) for r in cur.fetchall()]
    if info and customers:
        import numpy as np
        try:
            bundle=artifact('segments.joblib');values=np.log1p([[max(0,r['recencia']),r['frecuencia'],float(r['monetario'])] for r in customers]);groups=bundle['model'].predict(values)
            for row,group in zip(customers,groups):row['segmento']=bundle['labels'][int(group)]
        except HTTPException as exc:status=str(exc.detail)
    return serial({'kpi':kpi,'predicciones':forecasts,'segmentos':customers,'modelo':info,'estado_modelo':status,'periodo':'Últimos 30 días para KPI; RFM últimos 365 días; predicción para hoy','limites':'Hasta 100 combinaciones producto/sucursal y 500 clientes autorizados. Las predicciones no descuentan inventario ni generan pedidos.'})
