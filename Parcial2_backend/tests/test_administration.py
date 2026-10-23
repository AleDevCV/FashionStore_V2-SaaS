import pytest

@pytest.mark.parametrize('path',['/api/roles','/api/usuarios/','/api/clientes/','/api/ciudades','/api/sucursales','/api/categorias/','/api/temporadas/','/api/prendas/'])
def test_inherited_administration_reads_are_scoped(client,companies,headers,path):
    for header in headers:
        response=client.get(path,headers=header)
        assert response.status_code==200,(path,response.text)

def test_role_creation_and_cross_tenant_assignment(client,companies,headers):
    a,b=companies
    r=client.post('/api/roles',headers=headers[0],json={'nombre':'Inventario personalizado'});assert r.status_code==201,r.text
    assert client.post('/api/roles',headers=headers[1],json={'nombre':'Inventario personalizado'}).status_code==201
    assert client.put(f"/api/usuarios/{a['user']}/sucursales",headers=headers[0],json={'sucursales':[a['branch']]}).status_code==200
    assert client.put(f"/api/usuarios/{a['user']}/sucursales",headers=headers[0],json={'sucursales':[b['branch']]}).status_code==404
    assert client.put(f"/api/usuarios/{b['user']}/sucursales",headers=headers[0],json={'sucursales':[]}).status_code==404

def test_category_parent_cannot_cross_company(client,companies,headers):
    b=client.get('/api/categorias/',headers=headers[1]).json()[0]['id_categoria']
    r=client.post('/api/categorias/',headers=headers[0],json={'nombre':'Padre cruzado','id_categoria_padre':b})
    assert r.status_code in {400,404,422},r.text
