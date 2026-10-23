from datetime import datetime,timedelta
import math
from conftest import owner_connection
from app.ml_features import demand_features

def history(c):
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(c['tenant']),))
        for day in range(35,0,-1):
            stamp=datetime.now()-timedelta(days=day)
            cur.execute("INSERT INTO venta(id_cliente,id_sucursal,id_cajero,tipo_venta,metodo_pago,subtotal,total,fecha_venta,fecha_entrega,origen_datos) VALUES(%s,%s,%s,'Presencial','Efectivo',50,50,%s,%s,'demostracion') RETURNING id_venta",(c['customer'],c['branch'],c['user'],stamp,stamp));sale=cur.fetchone()['id_venta']
            cur.execute('INSERT INTO detalle_venta(id_venta,id_variante_prenda,cantidad,precio_unitario,subtotal) VALUES(%s,%s,1,50,50)',(sale,c['variant']))

def test_inference_real_tenant_history_and_versioned_models(client,companies,headers):
    history(companies[0])
    r=client.get('/api/analitica/dashboard',headers=headers[0]);assert r.status_code==200,r.text
    result=r.json();assert result['kpi']['ventas_demostracion']>0
    assert result['modelo']['version']=='v1'
    prediction=result['predicciones'][0]['prediccion'];assert prediction is not None and math.isfinite(prediction) and prediction>=0
    other=client.get('/api/analitica/dashboard',headers=headers[1]).json();assert other['kpi']['ventas']==0 and other['predicciones'][0]['prediccion'] is None
    assert client.get('/api/analitica/dashboard',headers=headers[0],params={'sucursal':companies[1]['branch']}).status_code==404

def test_features_only_use_history_and_target_calendar():
    from datetime import date
    row=demand_features([1]*28,date(2026,10,23),50)
    assert row[:4]==[1,1,1,1] and len(row)==10

def test_artifact_integrity_denies_untrusted_bytes(tmp_path,monkeypatch):
    import json
    from fastapi import HTTPException
    from app.services import analytics
    import pytest
    original=analytics.metadata();(tmp_path/'metadata.json').write_text(json.dumps(original));(tmp_path/'demand.joblib').write_bytes(b'not-a-trusted-model')
    monkeypatch.setattr(analytics,'DIRECTORY',tmp_path);analytics.artifact.cache_clear()
    with pytest.raises(HTTPException) as err:analytics.artifact('demand.joblib')
    assert err.value.status_code==503
    analytics.artifact.cache_clear()


def test_artifact_requires_training_dependency_versions(monkeypatch):
    from fastapi import HTTPException
    from app.services import analytics
    import joblib,pytest
    original=analytics.metadata();original['numpy']='incompatible-test-version'
    monkeypatch.setattr(analytics,'metadata',lambda:original)
    def forbidden_load(*args,**kwargs):raise AssertionError('No deserializar un modelo incompatible.')
    monkeypatch.setattr(joblib,'load',forbidden_load)
    analytics.artifact.cache_clear()
    try:
        with pytest.raises(HTTPException) as err:analytics.artifact('demand.joblib')
        assert err.value.status_code==503
    finally:analytics.artifact.cache_clear()
