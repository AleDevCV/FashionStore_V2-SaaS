from conftest import owner_connection

def test_multicolor_combinations_share_primary_color_without_merging_stock(client,companies,headers):
    c=companies[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id',%s,true)",(str(c['tenant']),))
        cur.execute('SELECT id_talla,id_color FROM variante_prenda WHERE id_variante_prenda=%s',(c['variant'],));base=cur.fetchone()
        cur.execute("INSERT INTO color(nombre) VALUES('Rojo'),('Verde') RETURNING id_color");extra=[r['id_color'] for r in cur.fetchall()]
        cur.execute('SELECT id_categoria FROM prenda WHERE id_prenda=%s',(c['product'],));category=cur.fetchone()['id_categoria']
    body={'sku':'MULTICOLOR','nombre':'Camisa bicolor','precio_base':90,'id_categoria':category,'material':'Algodón','medidas':'M: 100cm contorno','variantes':[{'id_talla':base['id_talla'],'id_color':base['id_color'],'color_ids':[color],'stock_inicial':3} for color in extra]}
    r=client.post('/api/prendas',headers=headers[0],json=body);assert r.status_code==201,r.text
    variants=r.json()['variantes'];assert len(variants)==2 and all(len(v['color_ids'])==2 and v['stock_total']==3 for v in variants)
    assert len(set(v['sku_variante'] for v in variants))==2
    public=client.get('/api/catalogo',headers={'X-Empresa':c['slug']},params={'id_color':extra[0]}).json();assert public['total']==1
    assert len(public['prendas'][0]['variantes'])==1 and 'Rojo' in public['prendas'][0]['variantes'][0]['color']

def test_color_of_another_tenant_cannot_be_linked(client,companies,headers):
    c=companies[0]
    with owner_connection() as conn,conn.cursor() as cur:
        cur.execute('SELECT id_talla,id_color FROM variante_prenda WHERE id_variante_prenda=%s',(c['variant'],));base=cur.fetchone()
        cur.execute('SELECT id_categoria FROM prenda WHERE id_prenda=%s',(c['product'],));cat=cur.fetchone()['id_categoria']
        cur.execute('SELECT id_color FROM variante_prenda WHERE id_variante_prenda=%s',(companies[1]['variant'],));foreign=cur.fetchone()['id_color']
    r=client.post('/api/prendas',headers=headers[0],json={'sku':'COLORS','nombre':'No válido','precio_base':50,'id_categoria':cat,'variantes':[{'id_talla':base['id_talla'],'id_color':base['id_color'],'color_ids':[foreign]}]})
    assert r.status_code in {400,422},r.text

def test_public_catalogue_uses_current_offer_price(client,companies,headers):
    c=companies[0]
    r=client.put('/api/prendas/'+str(c['product']),headers=headers[0],json={'precio_oferta':40,'oferta_inicio':'2026-01-01','oferta_fin':'2027-12-31','admite_cambio':False})
    assert r.status_code==200 and r.json()['admite_cambio'] is False
    data=client.get('/api/catalogo/'+str(c['product']),headers={'X-Empresa':c['slug']}).json()
    assert float(data['variantes'][0]['precio'])==40 and data['precio_oferta'] is not None
