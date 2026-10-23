import { Component, inject } from '@angular/core';
import { AuthService } from './services/auth.service';

@Component({selector:'app-empresa-selector',standalone:true,
template:`<label class="company">Empresa<input aria-label="Identificador de empresa" [value]="slug" (change)="change($event)" pattern="[a-z0-9][a-z0-9-]{1,60}" placeholder="demo-a" autocomplete="organization" required><small>Usa el identificador de tu empresa. Administración del servicio: plataforma.</small></label>`,
styles:[`.company{display:grid;gap:8px;margin:20px 0;font-size:14px}.company input{padding:12px;border:1px solid #a4b3a8;border-radius:6px;background:#fff;color:#20392c;font:inherit}.company small{font-size:12px;color:#59665e}`]})
export class EmpresaSelector {
  private auth=inject(AuthService);
  slug=localStorage.getItem('fashionstore_p2_empresa')||'demo-a';
  change(event:Event){const value=(event.target as HTMLInputElement).value.trim().toLowerCase();if(!/^[a-z0-9][a-z0-9-]{1,60}$/.test(value))return;if(value!==this.slug)this.auth.logout();this.slug=value;localStorage.setItem('fashionstore_p2_empresa',value);window.dispatchEvent(new Event('fashionstore-session'));}
}
