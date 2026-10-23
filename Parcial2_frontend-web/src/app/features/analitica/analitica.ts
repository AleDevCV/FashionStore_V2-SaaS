import {Component,OnInit,inject,signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {HttpClient,HttpParams} from '@angular/common/http';
import {firstValueFrom} from 'rxjs';
import {environment} from '../../../environments/environment';
@Component({selector:'app-analitica',standalone:true,imports:[CommonModule,FormsModule],templateUrl:'./analitica.html',styleUrls:['../reportes/reportes.scss','./analitica.scss']})
export class Analitica implements OnInit {
 private http=inject(HttpClient);result=signal<any>(null);branches=signal<any[]>([]);message=signal('');busy=signal(false);branch:number|null=null;
 async ngOnInit(){try{const ctx=await firstValueFrom(this.http.get<any>(environment.apiUrl+'/api/contexto'));this.branches.set(ctx.sucursales);await this.load();}catch(e:any){this.message.set(e.error?.detail||'No se pudo abrir la analítica.');}}
 async load(){this.busy.set(true);try{const params=this.branch?new HttpParams().set('sucursal',this.branch):undefined;this.result.set(await firstValueFrom(this.http.get<any>(environment.apiUrl+'/api/analitica/dashboard',{params})));this.message.set('');}catch(e:any){this.message.set(e.error?.detail||'No se pudo consultar la analítica.');}finally{this.busy.set(false);}}
}
