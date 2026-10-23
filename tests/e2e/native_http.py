"""Smoke HTTP acotado. DEMO_PASSWORD llega del entorno privado; no se imprime.

Ejecutar con las semillas demo ya instaladas. Escribe reportes de demostración y
su auditoría; no realiza ventas, pagos ni llamadas al proveedor generativo.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import statistics
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:2468')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    base = args.base.rstrip('/')
    password = os.environ['DEMO_PASSWORD']

    def call(path, company=None, token=None, data=None, expected=200):
        headers = {'Accept': 'application/json'}
        if company:
            headers['X-Empresa'] = company
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if data is not None:
            headers['Content-Type'] = 'application/json'
        request = Request(base + path, headers=headers,
                          data=json.dumps(data).encode() if data is not None else None)
        start = time.monotonic()
        try:
            response = urlopen(request, timeout=45)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            status = response.status
            content_type = response.headers.get('Content-Type', '')
        if status != expected:
            # No imprimir respuestas de login ni cuerpos con datos comerciales.
            raise AssertionError(f'{path}: estado {status}, esperado {expected}')
        result = json.loads(raw) if 'application/json' in content_type else raw
        return result, time.monotonic() - start

    call('/health')
    for path in ('/', '/login', '/ngsw.json', '/ngsw-worker.js', '/manifest.webmanifest'):
        body, _ = call(path)
        assert body
    call('/.env', expected=403)
    call('/api/contexto', expected=400)
    tokens, contexts, variants = {}, {}, {}
    for company in ('demo-a', 'demo-b'):
        login, _ = call('/api/login', company, data={
            'correo': 'admin@example.com', 'password': password})
        tokens[company] = login['access_token']
        context, _ = call('/api/contexto', token=tokens[company])
        assert context['empresa']['slug'] == company
        contexts[company] = context
        branch = context['sucursales'][0]['id_sucursal']
        catalog, _ = call(f'/api/offline/catalogo?branch_id={branch}', token=tokens[company])
        assert catalog['tenant_id'] == context['empresa']['id_empresa']
        assert len(catalog['products']) == 12
        variants[company] = {row['id_variante_prenda'] for row in catalog['products']}
    assert contexts['demo-a']['empresa']['id_empresa'] != contexts['demo-b']['empresa']['id_empresa']
    assert not variants['demo-a'].intersection(variants['demo-b'])
    branch_b = contexts['demo-b']['sucursales'][0]['id_sucursal']
    call(f'/api/offline/catalogo?branch_id={branch_b}', token=tokens['demo-a'], expected=404)
    call('/api/reportes/generativo', token=tokens['demo-a'],
         data={'texto': 'Ventas del último mes por sucursal'}, expected=403)
    report, _ = call('/api/reportes/convencional', token=tokens['demo-b'],
                     data={'tipo': 'ventas_sucursal'})
    assert report['filas'] and report['ventas_demostracion'] > 0
    identifier = report['id']
    for extension, signature in (('pdf', b'%PDF-'), ('xlsx', b'PK')):
        document, _ = call(f'/api/reportes/{identifier}/exportar/{extension}', token=tokens['demo-b'])
        assert document.startswith(signature)
    call(f'/api/reportes/{identifier}', token=tokens['demo-a'], expected=404)
    dashboard, model_seconds = call('/api/analitica/dashboard', token=tokens['demo-b'])
    forecasts = [row for row in dashboard['predicciones'] if row['prediccion'] is not None]
    assert dashboard['estado_modelo'] == 'disponible' and forecasts
    assert any('segmento' in row for row in dashboard['segmentos'])

    def read_context(index):
        company = ('demo-a', 'demo-b')[index % 2]
        result, seconds = call('/api/contexto', token=tokens[company])
        assert result['empresa']['slug'] == company
        return seconds

    with ThreadPoolExecutor(max_workers=3) as executor:
        timings = list(executor.map(read_context, range(30)))
    evidence = {
        'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'base_url': base,
        'health_and_pwa_assets': True, 'private_dotfile_denied': True,
        'companies': 2, 'offline_catalog_variants_per_company': 12,
        'tenant_isolation_and_cross_report_denial': True,
        'basic_generative_denied_without_provider_call': True,
        'pdf_and_xlsx': True, 'native_ml_forecasts': len(forecasts),
        'native_ml_segments': len(dashboard['segmentos']),
        'first_dashboard_seconds': round(model_seconds, 3),
        'concurrency': {'workers': 3, 'requests': len(timings), 'failed': 0,
                        'median_seconds': round(statistics.median(timings), 3),
                        'max_seconds': round(max(timings), 3)},
        'limitations': 'Smoke y concurrencia breve; no es una prueba de carga sostenida ni de integraciones externas.',
    }
    args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('HTTP/PWA, dos empresas, aislamiento, reportes, ML y 30 consultas con concurrencia 3: aprobados.')


if __name__ == '__main__':
    main()
