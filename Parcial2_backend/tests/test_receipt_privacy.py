from test_commerce import pos_body

def test_receipt_download_requires_tenant_and_identity(client,companies,headers):
    r=client.post('/api/pos/ventas',headers=headers[0],json=pos_body(companies[0]));assert r.status_code==201,r.text
    data=r.json();assert data['url_pdf'],data
    url=data['url_pdf'];assert url.startswith('/api/comprobantes/') and url.endswith('/pdf')
    r=client.get(url,headers=headers[0]);assert r.status_code==200,r.text
    assert r.content.startswith(b'%PDF')
    assert client.get(url,headers=headers[1]).status_code==404
    assert client.get(url,headers={'X-Empresa':companies[0]['slug']}).status_code==401
