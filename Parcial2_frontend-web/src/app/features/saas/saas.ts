import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

@Component({
  standalone: true, selector: 'app-saas', imports: [CommonModule, FormsModule],
  template: `
    <main class="atelier">
      <p class="eyebrow">FASHIONSTORE / ADMINISTRACIÓN</p>
      <h1>Tu empresa, en contexto.</h1>
      <p class="intro">Gestiona el servicio y consulta los límites de tu espacio de trabajo.</p>
      @if (message()) { <p role="status" class="notice">{{message()}}</p> }
      @if (context(); as ctx) {
        <section class="summary"><div><span>Empresa activa</span><h2>{{ctx.empresa.nombre}}</h2><p>{{ctx.empresa.slug}}</p></div>
          <div><span>Plan contratado</span><h2>{{ctx.suscripcion?.plan || 'Plataforma'}}</h2><p>{{ctx.suscripcion?.vigente ? 'Suscripción vigente' : 'Consulta de administración'}}</p></div>
          <div><span>Sucursales autorizadas</span><h2>{{ctx.sucursales.length}}</h2><p>Permisos validados por el servidor</p></div></section>
        @if (ctx.empresa.plataforma) {
          <section><h2>Registrar empresa</h2><form (ngSubmit)="createCompany()">
            <label>Nombre<input name="nombre" [(ngModel)]="company.nombre" required maxlength="150"></label>
            <label>Identificador público<input name="slug" [(ngModel)]="company.slug" required pattern="[a-z0-9][a-z0-9-]{1,60}"></label>
            <label>Correo administrador<input name="email" type="email" [(ngModel)]="company.correo_admin" required></label>
            <label>Contraseña inicial<input name="password" type="password" [(ngModel)]="company.password_admin" minlength="12" required autocomplete="new-password"></label>
            <label>Plan<select name="plan" [(ngModel)]="company.id_plan">@for (plan of plans(); track plan.id_plan) {<option [ngValue]="plan.id_plan">{{plan.nombre}}</option>}</select></label>
            <button [disabled]="busy()">Registrar empresa</button></form></section>
          <section><h2>Planes del servicio</h2><div class="plans">@for (plan of plans(); track plan.id_plan) {
            <article><h3>{{plan.nombre}}</h3><label>Sucursales activas<input type="number" min="1" [(ngModel)]="plan.max_sucursales"></label>
              <label><input type="checkbox" [(ngModel)]="plan.reportes_ia"> Reportes generativos</label><button (click)="savePlan(plan)">Guardar límites</button></article>
          }</div></section>
          <section><h2>Empresas registradas</h2><div class="table-scroll"><table><thead><tr><th>Empresa</th><th>Identificador</th><th>Estado</th><th>Acción</th></tr></thead><tbody>
            @for (item of companies(); track item.id_empresa) {<tr><td>{{item.nombre}}</td><td>{{item.slug}}</td><td>{{item.activa ? 'Activa' : 'Suspendida'}}</td><td><button (click)="toggleCompany(item)">{{item.activa ? 'Suspender' : 'Activar'}}</button></td></tr>}
          </tbody></table></div></section>
          <section><h2>Asignar o renovar suscripción</h2><form (ngSubmit)="saveSubscription()">
            <label>Empresa<select name="tenant" [(ngModel)]="subscription.tenant">@for(item of companies(); track item.id_empresa){<option [ngValue]="item.id_empresa">{{item.nombre}}</option>}</select></label>
            <label>Plan<select name="subscriptionplan" [(ngModel)]="subscription.id_plan">@for(plan of plans(); track plan.id_plan){<option [ngValue]="plan.id_plan">{{plan.nombre}}</option>}</select></label>
            <label>Inicio<input name="inicio" type="datetime-local" [(ngModel)]="subscription.inicio" required></label>
            <label>Vencimiento<input name="fin" type="datetime-local" [(ngModel)]="subscription.vencimiento" required></label><button [disabled]="busy()">Guardar suscripción</button>
          </form></section>
        } @else {
          <section><h2>Tu suscripción</h2><p>Vence: {{ctx.suscripcion?.vencimiento | date:'medium'}}</p><p>Máximo de sucursales: {{ctx.suscripcion?.max_sucursales}}</p><p>Reportes generativos: {{ctx.suscripcion?.reportes_ia ? 'Habilitados' : 'Requieren Profesional'}}</p></section>
        }
      }
    </main>`,
  styles: [`:host{display:block}.atelier{max-width:1180px;margin:auto;padding:40px 24px;color:#20392c;background:#faf9f4;min-height:100vh}h1,h2,h3{font-family:Georgia,serif;font-weight:400}h1{font-size:clamp(32px,4vw,52px);margin:12px 0}.eyebrow{font-size:11px;letter-spacing:3px}.intro{color:#59665e;margin-bottom:32px}section{margin:24px 0;padding:26px;border:1px solid #d8dfd8;border-radius:8px;background:white}.summary,.plans,form{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:24px}.summary h2{font-size:28px;margin:10px 0}.summary span,label{font-size:13px;color:#536357}label{display:flex;flex-direction:column;gap:8px}input,select{padding:12px;border:1px solid #a8b8ac;border-radius:4px;color:#20392c;font:inherit}input[type=checkbox]{width:20px;height:20px}button{padding:12px 20px;background:#204d36;color:white;border:0;border-radius:4px;cursor:pointer;align-self:end}button:disabled{opacity:.5;cursor:wait}.notice{padding:16px;background:#edf0df;border-left:4px solid #6d7a3e}.table-scroll{overflow-x:auto}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:14px;border-bottom:1px solid #d8dfd8}article{border:1px solid #d8dfd8;padding:20px}article label{margin:12px 0}a,button,input,select{outline-offset:4px}`]
})
export class Saas {
  private http=inject(HttpClient); private base=environment.apiUrl+'/api';
  context=signal<any>(null); plans=signal<any[]>([]); companies=signal<any[]>([]); message=signal('');busy=signal(false);
  company={nombre:'',slug:'',correo_admin:'',password_admin:'',id_plan:1};
  subscription={tenant:0,id_plan:1,inicio:'',vencimiento:''};
  constructor(){this.load();}
  private fail=(error:any)=>{this.message.set(typeof error.error?.detail==='string'?error.error.detail:'No fue posible completar la operación.');this.busy.set(false);};
  load(){this.http.get<any>(this.base+'/contexto').subscribe({next:ctx=>{this.context.set(ctx);if(ctx.empresa.plataforma)this.http.get<any[]>(this.base+'/empresas').subscribe({next:x=>this.companies.set(x),error:this.fail});},error:this.fail});this.http.get<any[]>(this.base+'/planes').subscribe({next:x=>this.plans.set(x),error:this.fail});}
  createCompany(){this.busy.set(true);this.http.post(this.base+'/empresas',this.company).subscribe({next:()=>{this.company.password_admin='';this.message.set('Empresa registrada.');this.busy.set(false);this.load();},error:this.fail});}
  savePlan(plan:any){this.http.patch(this.base+'/planes/'+plan.id_plan,{max_sucursales:plan.max_sucursales,reportes_ia:plan.reportes_ia}).subscribe({next:()=>{this.message.set('Límites actualizados.');this.load();},error:this.fail});}
  toggleCompany(item:any){this.http.patch(this.base+'/empresas/'+item.id_empresa+'?activa='+!item.activa,{}).subscribe({next:()=>this.load(),error:this.fail});}
  saveSubscription(){this.busy.set(true);this.http.put(this.base+'/suscripciones/'+this.subscription.tenant,{id_plan:this.subscription.id_plan,inicio:new Date(this.subscription.inicio).toISOString(),vencimiento:new Date(this.subscription.vencimiento).toISOString()}).subscribe({next:()=>{this.message.set('Suscripción actualizada.');this.busy.set(false);this.load();},error:this.fail});}
}
