from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_frontend-web/src/app/app.routes.ts';s=p.read_text(encoding='utf-8')
if "path: 'cambios'" not in s:
 s=s.replace('export const routes: Routes = [',"export const routes: Routes = [\n  {path: 'cambios', canActivate: [authGuard], title: 'Cambios y devoluciones', loadComponent: () => import('./features/cambios/cambios').then(m => m.Cambios)},")
 s=s.replace('children: [',"children: [\n      {path: 'cambios', title: 'Cambios y devoluciones', loadComponent: () => import('./features/cambios/cambios').then(m => m.Cambios)},",1)
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_frontend-web/src/app/layout/layout.html';s=p.read_text(encoding='utf-8')
if 'routerLink="/panel/cambios"' not in s:s=s.replace('<ul class="admin__nav-list">','<ul class="admin__nav-list">\n        <li><a class="admin__link" routerLink="/panel/cambios">Cambios y devoluciones</a></li>',1)
p.write_text(s,encoding='utf-8')
print('Pantallas de cambios disponibles para cliente y personal.')
