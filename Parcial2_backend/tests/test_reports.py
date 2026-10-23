import io
from datetime import date,timedelta
import pytest
from conftest import owner_connection
from app.schemas.reports import ReportIntent,ReportFilters

def sell(client,c,h):
    r=client.post('/api/pos/ventas',headers=h,json={'id_sucursal':c['branch'],'id_cliente':c['customer'],'items':[{'id_variante_prenda':c['variant'],'cantidad':1,'precio_unitario':50}],'metodo_pago':'Efectivo','monto_recibido':50})
    if r.status_code==404:r=client.post('/api/pos/ventas/',headers=h,json={'id_sucursal':c['branch'],'id_cliente':c['customer'],'items':[{'id_variante_prenda':c['variant'],'cantidad':1,'precio_unitario':50}],'metodo_pago':'Efectivo','monto_recibido':50})
    assert r.status_code in (200,201),r.text

@pytest.mark.parametrize('kind',['ventas_sucursal','productos_vendidos','evolucion_ventas','stock_bajo','ingresos_categoria','comparacion_sucursales'])
def test_six_templates_real_data_and_tenant_scope(client,companies,headers,kind):
    c=companies[0];sell(client,c,headers[0]);sell(client,companies[1],headers[1])
    r=client.post('/api/reportes/convencional',headers=headers[0],json={'tipo':kind,'sucursal':c['branch']});assert r.status_code==200,r.text
    report=r.json();assert len(report['filas'])==1
    row=report['filas'][0]
    if kind=='stock_bajo':assert row['disponible']==4
    elif kind=='comparacion_sucursales':assert row['ingresos_actuales']=='50.00' and row['ingresos_anteriores']=='0.00'
    else:assert row['ingresos']=='50.00'
    assert client.get('/api/reportes/'+report['id'],headers=headers[1]).status_code==404
    assert client.post('/api/reportes/convencional',headers=headers[0],json={'tipo':kind,'sucursal':companies[1]['branch']}).status_code==404

def test_exports_use_saved_results_and_protect_spreadsheet_strings(client,companies,headers):
    c=companies[0]
    with owner_connection() as conn,conn.cursor() as cur:cur.execute("UPDATE prenda SET nombre='=HYPERLINK(\"https://example.invalid\")' WHERE id_prenda=%s",(c['product'],))
    sell(client,c,headers[0]);report=client.post('/api/reportes/convencional',headers=headers[0],json={'tipo':'productos_vendidos'}).json()
    with owner_connection() as conn,conn.cursor() as cur:cur.execute('UPDATE detalle_venta SET subtotal=999 WHERE tenant_id=%s',(c['tenant'],))
    pdf=client.get('/api/reportes/'+report['id']+'/exportar/pdf',headers=headers[0]);assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
    xlsx=client.get('/api/reportes/'+report['id']+'/exportar/xlsx',headers=headers[0]);assert xlsx.status_code==200,xlsx.text
    from openpyxl import load_workbook
    sheet=load_workbook(io.BytesIO(xlsx.content)).active
    assert sheet['B4'].value.startswith("'=") and sheet['D4'].value==50

def test_basic_cannot_use_generative_or_legacy_route(client,companies,headers,monkeypatch):
    from app.services import reports
    monkeypatch.setenv('GEMINI_API_KEY','dummy-not-a-live-key')
    assert client.post('/api/reportes/generativo',headers=headers[0],json={'texto':'ventas por sucursal'}).status_code==403
    assert client.post('/api/ia/analitica-voz',headers=headers[0],json={'texto_voz':'ventas por sucursal'}).status_code==403

def test_interpretation_validated_then_uses_same_template(client,companies,headers,monkeypatch):
    from app.services import reports
    c=companies[1];sell(client,c,headers[1])
    def fake(cur,text):
        reports.access(cur,True);return ReportIntent(estado='listo',mensaje='Ventas del período',filtros=ReportFilters(tipo='ventas_sucursal'))
    monkeypatch.setattr(reports,'interpret',fake)
    r=client.post('/api/reportes/generativo',headers=headers[1],json={'texto':'ventas por sucursal'});assert r.status_code==200,r.text
    assert r.json()['reporte']['filas'][0]['ingresos']=='50.00'

def test_ambiguity_returns_question_without_made_up_rows(client,companies,headers,monkeypatch):
    from app.services import reports
    monkeypatch.setattr(reports,'interpret',lambda cur,text:ReportIntent(estado='aclarar',mensaje='¿Qué período desea comparar?'))
    r=client.post('/api/reportes/generativo',headers=headers[1],json={'texto':'compara las sucursales'});assert r.status_code==200 and r.json()['reporte'] is None

def test_period_and_extra_sql_are_rejected(client,companies,headers):
    for payload in ({'tipo':'ventas_sucursal','sql':'SELECT * FROM usuario'},{'tipo':'ventas_sucursal','desde':'2020-01-01','hasta':'2026-01-01'}):
        assert client.post('/api/reportes/convencional',headers=headers[0],json=payload).status_code==422
