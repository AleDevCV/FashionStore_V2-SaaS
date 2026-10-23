from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
def change(path,old,new):
 p=ROOT/path;s=p.read_text(encoding='utf-8-sig')
 if new in s:return
 if old not in s:raise RuntimeError('Ancla ausente: '+path)
 p.write_text(s.replace(old,new,1),encoding='utf-8')

for p in (ROOT/'Parcial2_frontend-web/src/environments').glob('*.ts'):
 s=p.read_text(encoding='utf-8-sig')
 s=re.sub(r"apiToken:\s*'[^']*'","apiToken: ''",s)
 s=s.replace("'fashionstore_token'","'fashionstore_p2_token'")
 p.write_text(s,encoding='utf-8')
change('Parcial2_frontend-web/src/app/core/interceptors/auth.interceptor.ts',"const token = authService.obtenerToken();", """const token = authService.obtenerToken();
  if (solicitud.url.includes('/api/')) {
    solicitud = solicitud.clone({setHeaders: {'X-Empresa': localStorage.getItem('fashionstore_p2_empresa') || 'demo-a'}});
  }""")
change('Parcial2_frontend-web/src/app/core/interceptors/auth.interceptor.ts',"authService.logout();","authService.logout(false);")
change('Parcial2_frontend-web/src/app/core/interceptors/auth.interceptor.ts',"const esPeticionExcluida = esPeticionDeLogin || esPeticionRecuperacion;","const esPeticionExcluida = esPeticionDeLogin || esPeticionRecuperacion || solicitud.url.includes('/api/logout');")
change('Parcial2_frontend-web/src/app/core/services/auth.service.ts','logout(): void {', '''logout(revocar = true): void {
    const token = this.obtenerToken();
    if (revocar && token && navigator.onLine) {
      this.http.post(`${environment.apiUrl}/api/logout`, {}, {headers: {Authorization: `Bearer ${token}`}}).subscribe({error: () => {}});
    }''')
for name in ['login','login-cliente']:
 folder=f'Parcial2_frontend-web/src/app/features/auth/{name}'
 p=ROOT/folder/f'{name}.ts';s=p.read_text(encoding='utf-8-sig')
 if 'EmpresaSelector' not in s:
  s="import { EmpresaSelector } from '../../../core/empresa-selector';\n"+s
  s=s.replace('imports: [','imports: [EmpresaSelector, ',1);p.write_text(s,encoding='utf-8')
 p=ROOT/folder/f'{name}.html';s=p.read_text(encoding='utf-8-sig')
 if 'app-empresa-selector' not in s:
  s=s.replace('<form','<app-empresa-selector />\n      <form',1);p.write_text(s,encoding='utf-8')
change('Parcial2_frontend-web/src/app/app.routes.ts',"children: [","children: [\n      {path: 'saas', title: 'Empresa y suscripción', loadComponent: () => import('./features/saas/saas').then(m => m.Saas)},")
change('Parcial2_frontend-web/src/app/layout/layout.html','<ul class="admin__nav-list">','<ul class="admin__nav-list">\n        <li><a class="admin__link" routerLink="/panel/saas">Empresa y suscripción</a></li>')
change('Parcial2_mobile/lib/core/api_client.dart',"final String baseUrl;","final String baseUrl;\n  static String empresa = 'demo-a';")
change('Parcial2_mobile/lib/core/api_client.dart',"'Content-Type': 'application/json',","'Content-Type': 'application/json',\n      'X-Empresa': empresa,")
change('Parcial2_mobile/lib/features/login/login_screen.dart','final _correoCtrl = TextEditingController();',"final _correoCtrl = TextEditingController();\n  final _empresaCtrl = TextEditingController(text: ApiClient.empresa);")
change('Parcial2_mobile/lib/features/login/login_screen.dart','_correoCtrl.dispose();','_correoCtrl.dispose();\n    _empresaCtrl.dispose();')
change('Parcial2_mobile/lib/features/login/login_screen.dart','await _auth.login(',"ApiClient.empresa = _empresaCtrl.text.trim().toLowerCase();\n      await _auth.login(")
change('Parcial2_mobile/lib/features/login/login_screen.dart','controller: _correoCtrl,','controller: _correoCtrl,') if False else None
p=ROOT/'Parcial2_mobile/lib/features/login/login_screen.dart';s=p.read_text(encoding='utf-8-sig')
needle='''                    TextFormField(
                      controller: _correoCtrl,'''
if 'labelText: \'Empresa\'' not in s:
 s=s.replace(needle,"""                    TextFormField(controller: _empresaCtrl, decoration: const InputDecoration(labelText: 'Empresa', hintText: 'demo-a'), validator: (value) => value == null || !RegExp(r'^[a-z0-9][a-z0-9-]{1,60}$').hasMatch(value.trim()) ? 'Identificador de empresa requerido' : null),
                    const SizedBox(height: 16),
"""+needle,1)
 p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_mobile/lib/core/config.dart';s=p.read_text(encoding='utf-8-sig').replace('https://fashionstore.aledevcv.me','https://fashionstore-v2.aledevcv.me');p.write_text(s,encoding='utf-8')
print('Selección explícita de empresa, rutas SaaS y configuración V2 incorporadas.')
