import {Component,inject,signal,OnDestroy,OnInit} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {HttpClient} from '@angular/common/http';
import {firstValueFrom} from 'rxjs';
import {environment} from '../../../environments/environment';

@Component({selector:'app-reportes',standalone:true,imports:[CommonModule,FormsModule],templateUrl:'./reportes.html',styleUrl:'./reportes.scss'})
export class Reportes implements OnInit,OnDestroy {
 private http=inject(HttpClient);private base=environment.apiUrl+'/api';private recognition:any;
 types=signal<Record<string,string>>({});branches=signal<any[]>([]);pro=signal(false);busy=signal(false);message=signal('');result=signal<any>(null);listening=signal(false);
 filters={tipo:'ventas_sucursal',desde:new Date(Date.now()-30*86400000).toISOString().slice(0,10),hasta:new Date().toISOString().slice(0,10),sucursal:null as number|null,categoria:null as number|null,agrupacion:'dia',umbral:5,limite:100};text='';
 get entries(){return Object.entries(this.types());}
 get voice(){return !!((window as any).SpeechRecognition||(window as any).webkitSpeechRecognition);}
 async ngOnInit(){try{const [types,context]=await Promise.all([firstValueFrom(this.http.get<Record<string,string>>(this.base+'/reportes/tipos')),firstValueFrom(this.http.get<any>(this.base+'/contexto'))]);this.types.set(types);this.branches.set(context.sucursales);this.pro.set(context.suscripcion?.reportes_ia && context.suscripcion?.vigente);}catch(e:any){this.message.set(this.error(e));}}
 ngOnDestroy(){this.recognition?.abort();}
 async run(generative=false){if(this.busy())return;this.busy.set(true);this.message.set('Consultando datos de la empresa…');this.result.set(null);try{if(generative){const value=await firstValueFrom(this.http.post<any>(this.base+'/reportes/generativo',{texto:this.text}));this.message.set(value.intencion.mensaje);this.result.set(value.reporte);}else{this.result.set(await firstValueFrom(this.http.post<any>(this.base+'/reportes/convencional',this.filters)));this.message.set('Reporte generado con datos actuales.');}}catch(e:any){this.message.set(this.error(e));}finally{this.busy.set(false);}}
 dictate(){const Speech=(window as any).SpeechRecognition||(window as any).webkitSpeechRecognition;if(!Speech)return;this.recognition=new Speech();this.recognition.lang='es-BO';this.recognition.continuous=false;this.recognition.interimResults=false;this.recognition.onresult=(e:any)=>{this.text=e.results[0][0].transcript;this.listening.set(false);};this.recognition.onerror=()=>{this.message.set('No se pudo transcribir. Puedes escribir la solicitud.');this.listening.set(false);};this.recognition.onend=()=>this.listening.set(false);this.listening.set(true);this.recognition.start();}
 stop(){this.recognition?.stop();this.listening.set(false);}
 async export(format:'pdf'|'xlsx'){const result=this.result();try{const blob=await firstValueFrom(this.http.get(this.base+'/reportes/'+result.id+'/exportar/'+format,{responseType:'blob'}));const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='reporte-'+result.id+'.'+format;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e:any){this.message.set(this.error(e));}}
 get chart(){const r=this.result();if(!r?.filas.length)return [];const value=['ingresos','ingresos_actuales','unidades','disponible'].find(c=>r.columnas.includes(c));if(!value)return [];const max=Math.max(1,...r.filas.map((x:any)=>Number(x[value])));return r.filas.slice(0,20).map((x:any)=>({label:x.sucursal||x.producto||x.categoria||x.periodo,value:Number(x[value]),width:Math.max(1,Number(x[value])/max*100)}));}
 private error(e:any){return typeof e.error?.detail==='string'?e.error.detail:'No se pudo generar el reporte. Revisa el período, los permisos y la conexión.';}
}
