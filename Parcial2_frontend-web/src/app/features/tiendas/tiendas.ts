import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { environment } from '../../../environments/environment';

@Component({standalone:true, selector:'app-tiendas',imports:[CommonModule,RouterLink],
 template:`<main class="market"><header><a routerLink="/tiendas" class="brand">FASHIONSTORE</a>
 <nav>@if(auth.estaAutenticado()){<span>{{auth.usuarioActual()?.nombre}}</span><button class="text-button" (click)="logout()">Cerrar sesión</button>}@else{<a routerLink="/login">Iniciar sesión</a><a routerLink="/registro">Crear cuenta</a>}</nav></header>
 <section class="intro"><p class="eyebrow">UNA CUENTA. DISTINTAS FORMAS DE VESTIR.</p><h1>Encuentra tu próxima tienda.</h1>
 <p>Explora las colecciones de cada marca. Tu cuenta te acompaña en todas; cada tienda prepara y atiende sus propias compras.</p></section>
 @if(message()){<p class="notice" role="status">{{message()}}</p>}
 @if(loading()){<p role="status">Cargando tiendas…</p>}
 <section class="stores" aria-label="Tiendas disponibles">@for(store of stores();track store.id_empresa){
 <article><span class="eyebrow">COLECCIÓN / {{store.slug}}</span><h2>{{store.nombre}}</h2><p>Prendas, tallas y disponibilidad en sus sucursales.</p>
 <button (click)="enter(store.slug)" [disabled]="busy()">Explorar {{store.nombre}} <span aria-hidden="true">↗</span></button></article>
 }@empty{@if(!loading()){<p>No hay tiendas disponibles en este momento.</p>}}</section>
 @if(auth.obtenerRol()==='Cliente'){
 <section class="purchases"><div class="section-heading"><h2>Tus compras, en un solo lugar.</h2><button class="text-button" (click)="history()" [disabled]="busy()">Actualizar historial</button></div>
 <p>El historial muestra únicamente tus compras. Puedes entrar a cada tienda para consultar sus comprobantes, pedidos y cambios.</p>
 <div class="scroll"><table><thead><tr><th>Tienda</th><th>Compra</th><th>Fecha</th><th>Total</th><th></th></tr></thead><tbody>
 @for(sale of purchases();track sale.empresa+':'+sale.id_venta){<tr><td>{{sale.tienda}}</td><td>#{{sale.id_venta}}</td><td>{{sale.fecha_venta|date:'dd/MM/yyyy'}}</td><td>Bs {{sale.total|number:'1.2-2'}}</td><td><button class="text-button" (click)="enter(sale.empresa,'/mi-cuenta/pedidos')">Consultar</button></td></tr>}
 @empty{<tr><td colspan="5">Todavía no hay compras registradas en tu cuenta.</td></tr>}
 </tbody></table></div></section>}
 @if(auth.estaAutenticado()&&auth.obtenerRol()!=='Cliente'){<p><a routerLink="/panel">Volver a la administración de tu cuenta</a></p>}
 </main>`,
 styles:[`:host{display:block;background:#faf9f4;color:#22392d;min-height:100vh}.market{max-width:1180px;margin:auto;padding:28px 28px 70px}header,nav,.section-heading{display:flex;align-items:center;justify-content:space-between;gap:20px}header{padding-bottom:24px;border-bottom:1px solid #d9ddd4}.brand{font-size:18px;letter-spacing:4px;text-decoration:none;color:inherit}nav{font-size:14px;flex-wrap:wrap}.intro{max-width:760px;padding:64px 0 40px}.eyebrow{font-size:11px;letter-spacing:2px;color:#6b735e}h1,h2{font-family:Georgia,serif;font-weight:400}h1{font-size:clamp(36px,6vw,66px);line-height:1.06;margin:18px 0 24px}h2{font-size:30px}.intro>p:last-child{font-size:17px;line-height:1.7;max-width:650px}.stores{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px}article{border:1px solid #d4dccf;background:white;padding:30px}article:nth-child(even){background:#edf0e7}article p,.purchases>p{line-height:1.7;color:#566152}button{font:inherit;cursor:pointer;border:0;background:#244b35;color:white;padding:13px 18px}button span{margin-left:12px}button:disabled{opacity:.5;cursor:wait}.text-button{padding:7px 0;background:transparent;color:#244b35;text-decoration:underline;text-underline-offset:4px}.purchases{margin-top:58px;border-top:1px solid #d4dccf;padding-top:28px}.notice{padding:16px;background:#f2ead8;border-left:4px solid #8b7446}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:16px 12px;text-align:left;border-bottom:1px solid #d4dccf}a{color:#244b35;outline-offset:4px}button{outline-offset:4px}@media(max-width:600px){.market{padding:22px 18px}header,.section-heading{align-items:flex-start;flex-direction:column}.intro{padding-top:42px}article{padding:24px}}`]
})
export class Tiendas {
 readonly auth=inject(AuthService);private http=inject(HttpClient);private router=inject(Router);
 stores=signal<any[]>([]);purchases=signal<any[]>([]);message=signal('');loading=signal(true);busy=signal(false);
 constructor(){this.http.get<any[]>(environment.apiUrl+'/api/tiendas').subscribe({next:data=>{this.stores.set(data);this.loading.set(false);},error:()=>{this.message.set('No fue posible cargar las tiendas. Reintenta cuando tengas conexión.');this.loading.set(false);}});if(this.auth.obtenerRol()==='Cliente')this.history();}
 async enter(empresa:string,destination='/catalogo'){
  if(this.busy())return;this.busy.set(true);this.message.set('');
  try{if(this.auth.obtenerRol()==='Cliente')await firstValueFrom(this.auth.seleccionarTienda(empresa));
   localStorage.setItem('fashionstore_p2_empresa',empresa);await this.router.navigate([destination],{queryParams:{empresa}});
  }catch(e:any){this.message.set(typeof e.error?.detail==='string'?e.error.detail:'No fue posible abrir la tienda. Tus operaciones guardadas se conservan.');}finally{this.busy.set(false);}
 }
 async history(){try{this.purchases.set(await firstValueFrom(this.http.get<any[]>(environment.apiUrl+'/api/cuenta/compras')));}catch(e:any){this.message.set(typeof e.error?.detail==='string'?e.error.detail:'No fue posible cargar tu historial.');}}
 logout(){this.auth.logout();this.purchases.set([]);this.router.navigate(['/login']);}
}
