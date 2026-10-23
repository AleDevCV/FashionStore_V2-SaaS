import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NotificacionService } from './notificacion.service';
import { environment } from '../../../environments/environment';

@Injectable({providedIn:'root'})
export class DescargaService {
  private http=inject(HttpClient);private notice=inject(NotificacionService);
  abrir(url:string):void {
    const path=new URL(url,location.origin).pathname;
    if(!/^\/api\/comprobantes\/[^/]+\/pdf$/.test(path)){this.notice.error('El comprobante necesita regenerarse en la versión SaaS.');return;}
    this.http.get(environment.apiUrl+path,{responseType:'blob'}).subscribe({next:blob=>{
      const object=URL.createObjectURL(blob);const a=document.createElement('a');a.href=object;a.download=decodeURIComponent(path.split('/')[3])+'.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(object),1000);
    },error:()=>this.notice.error('No se pudo descargar el comprobante autorizado.')});
  }
}
