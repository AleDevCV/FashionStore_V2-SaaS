from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'Parcial2_frontend-web/src/app/core/models/catalogo.model.ts';s=p.read_text(encoding='utf-8')
fields='''  material?: string | null;
  medidas?: string | null;
  precio_mayorista?: number | string | null;
  umbral_mayorista?: number | null;
  precio_oferta?: number | string | null;
  oferta_inicio?: string | null;
  oferta_fin?: string | null;
'''
for name in ['Prenda','PrendaCrear']:
 needle=f'export interface {name} {{'
 if needle+'\n'+fields not in s:s=s.replace(needle,needle+'\n'+fields)
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_frontend-web/src/app/features/prendas/prenda-modal/prenda-modal.ts';s=p.read_text(encoding='utf-8')
if 'material: [prendaActual?' not in s:
 s=s.replace("descripcion: [prendaActual?.descripcion ?? ''],","""descripcion: [prendaActual?.descripcion ?? ''],
      material: [prendaActual?.material ?? ''],
      medidas: [prendaActual?.medidas ?? ''],
      precio_mayorista: [prendaActual?.precio_mayorista ?? null, [Validators.min(0)]],
      umbral_mayorista: [prendaActual?.umbral_mayorista ?? 6, [Validators.min(1)]],
      precio_oferta: [prendaActual?.precio_oferta ?? null, [Validators.min(0)]],
      oferta_inicio: [prendaActual?.oferta_inicio ?? null],
      oferta_fin: [prendaActual?.oferta_fin ?? null],""")
 s=s.replace('const valores = this.formulario.value;', '''const valores = this.formulario.value;
    const comercial = {
      material: valores.material || null, medidas: valores.medidas || null,
      precio_mayorista: valores.precio_mayorista === null || valores.precio_mayorista === '' ? null : Number(valores.precio_mayorista),
      umbral_mayorista: Number(valores.umbral_mayorista || 6),
      precio_oferta: valores.precio_oferta === null || valores.precio_oferta === '' ? null : Number(valores.precio_oferta),
      oferta_inicio: valores.oferta_inicio || null, oferta_fin: valores.oferta_fin || null,
    };''')
 s=s.replace('precio_base: Number(valores.precio_base),','precio_base: Number(valores.precio_base),\n          ...comercial,')
p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_frontend-web/src/app/features/prendas/prenda-modal/prenda-modal.html';s=p.read_text(encoding='utf-8')
if 'Condiciones comerciales' not in s:
 pos=s.rfind('</form>')
 extra='''<fieldset style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;padding:20px;margin:20px 0;border:1px solid #d8dfd8">
<legend>Condiciones comerciales</legend>
<label>Material<input class="fs-input" formControlName="material" maxlength="300"></label>
<label>Medidas<input class="fs-input" formControlName="medidas" maxlength="500"></label>
<label>Precio mayorista<input class="fs-input" type="number" min="0" step="0.01" formControlName="precio_mayorista"></label>
<label>Unidades para mayorista<input class="fs-input" type="number" min="1" formControlName="umbral_mayorista"></label>
<label>Precio de oferta<input class="fs-input" type="number" min="0" step="0.01" formControlName="precio_oferta"></label>
<label>Inicio de oferta<input class="fs-input" type="date" formControlName="oferta_inicio"></label>
<label>Fin de oferta<input class="fs-input" type="date" formControlName="oferta_fin"></label>
</fieldset>'''
 if pos<0:raise RuntimeError('Formulario de prendas no encontrado')
 s=s[:pos]+extra+s[pos:]
p.write_text(s,encoding='utf-8')
# Correcciones concretas de análisis móvil heredado.
p=ROOT/'Parcial2_mobile/lib/features/catalogo/catalogo_screen.dart';s=p.read_text(encoding='utf-8').replace("import '../ar/vestidor_virtual_screen.dart';\n",'');p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_mobile/lib/features/checkout/checkout_screen.dart';s=p.read_text(encoding='utf-8').replace('      // Abrir la pasarela dentro de la app','      if (!mounted) return;\n      // Abrir la pasarela dentro de la app');p.write_text(s,encoding='utf-8')
p=ROOT/'Parcial2_mobile/lib/features/checkout/stripe_webview_screen.dart';s=p.read_text(encoding='utf-8').replace('    Key? key,','    super.key,').replace('  }) : super(key: key);','  });').replace('              print("StripeWebview intercepted URL: $url");\n','');p.write_text(s,encoding='utf-8')
print('Formulario comercial y advertencias móviles corregidos.')
