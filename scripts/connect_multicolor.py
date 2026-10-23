"""Conecta la matriz de colores sin alterar las variantes ni compras existentes."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(relative,fn):
    p=ROOT/relative;p.write_text(fn(p.read_text(encoding='utf-8-sig')),encoding='utf-8')
def service(s):
    s=s.replace('p.precio_base, p.material','p.admite_cambio, p.precio_base, p.material')
    s=s.replace('v.id_color,\n                col.nombre AS color,','v.id_color, v.color_ids,\n                variant_color_label(v.id_variante_prenda) AS color,')
    s=s.replace("('material','medidas','precio_mayorista'","('admite_cambio','material','medidas','precio_mayorista'")
    s=s.replace('    sku_variante = f"{sku_prenda}-T{variante[\'id_talla\']}-C{variante[\'id_color\']}"',"    colors=sorted(set([variante['id_color'],*variante.get('color_ids',[])]))\n    sku_variante=f\"{sku_prenda}-T{variante['id_talla']}-C\"+'-'.join(str(c) for c in colors)")
    s=s.replace('(id_prenda, id_talla, id_color, sku_variante, precio_adicional)\n        VALUES (%s, %s, %s, %s, %s)','(id_prenda, id_talla, id_color, sku_variante, precio_adicional, color_ids)\n        VALUES (%s, %s, %s, %s, %s, %s)')
    s=s.replace('variante.get("precio_adicional", 0),\n        ),','variante.get("precio_adicional", 0), colors,\n        ),')
    s=s.replace('(id_sucursal, id_variante, stock),','(id_sucursal, id_variante, 0),')
    s=s.replace('    return id_variante\n',"        if stock>0:\n            from app.tenant import require_context\n            cursor.execute(\"INSERT INTO movimiento_inventario(id_sucursal,id_variante_prenda,tipo,cantidad,motivo,id_usuario) VALUES(%s,%s,'Entrada',%s,'Existencia inicial de variante',%s)\",(id_sucursal,id_variante,stock,require_context().user_id))\n    return id_variante\n")
    s=s.replace('SELECT id_sucursal FROM sucursal ORDER BY id_sucursal;','SELECT id_sucursal FROM sucursal WHERE activa AND branch_visible(id_sucursal) ORDER BY id_sucursal;')
    return s
edit('Parcial2_backend/app/services/prenda_service.py',service)
edit('Parcial2_backend/app/routers/prendas.py',lambda s:s.replace('[(v.id_talla, v.id_color) for v in datos.variantes]','[(v.id_talla, tuple(sorted(set([v.id_color,*v.color_ids])))) for v in datos.variantes]'))
def catalog(s):
    s=s.replace('col.nombre AS color','variant_color_label(v.id_variante_prenda) AS color')
    s=s.replace('v.id_color = %s','EXISTS(SELECT 1 FROM variante_color vc WHERE vc.id_variante_prenda=v.id_variante_prenda AND vc.id_color=%s)')
    s=s.replace('JOIN variante_prenda v ON v.id_color = col.id_color','JOIN variante_color vc ON vc.id_color=col.id_color JOIN variante_prenda v ON v.id_variante_prenda=vc.id_variante_prenda')
    s=s.replace('p.precio_base,','p.precio_base, p.material, p.medidas, p.precio_mayorista, p.umbral_mayorista, p.precio_oferta, p.oferta_inicio, p.oferta_fin,')
    s=s.replace('    variantes: list[dict[str, Any]] = []','    from app.services.commerce import price_for\n    cursor.execute(\'SELECT * FROM prenda WHERE id_prenda=%s\',(id_prenda,));commercial=dict(cursor.fetchone())\n    variantes: list[dict[str, Any]] = []')
    s=s.replace('variante["precio"] = precio_base + (variante.pop("precio_adicional") or 0)','variante["precio"] = price_for({**commercial,"precio_adicional":variante.pop("precio_adicional") or 0},1)')
    return s
edit('Parcial2_backend/app/services/catalogo_service.py',catalog)
edit('Parcial2_backend/app/schemas/catalogo.py',lambda s:s.replace('class PrendaCatalogo(BaseModel):','from app.schemas.prenda import ComercialFields\n\nclass PrendaCatalogo(ComercialFields):'))
edit('Parcial2_backend/app/routers/offline.py',lambda s:s.replace('c.nombre AS color','variant_color_label(v.id_variante_prenda) AS color'))
edit('Parcial2_backend/app/services/ia_service.py',lambda s:s.replace("STRING_AGG(DISTINCT col.nombre, ', ')","STRING_AGG(DISTINCT variant_color_label(vp.id_variante_prenda), ', ')"))
def ui(s):
    s=s.replace('  id_color: number;','  id_color: number;\n  color_ids: number[];',1)
    s=s.replace("      medidas: [prendaActual?.medidas ?? ''],","      medidas: [prendaActual?.medidas ?? ''],\n      admite_cambio:[prendaActual?.admite_cambio ?? true],")
    s=s.replace('      id_color: [null, [Validators.required]],','      id_color: [null, [Validators.required]],\n      color_ids:[[]],')
    s=s.replace('      material: valores.material || null,','      admite_cambio:valores.admite_cambio,\n      material: valores.material || null,')
    s=s.replace('        id_color: Number(fila.id_color),','        id_color: Number(fila.id_color),\n        color_ids: (fila.color_ids||[]).map(Number),')
    return s
edit('Parcial2_frontend-web/src/app/features/prendas/prenda-modal/prenda-modal.ts',ui)
def template(s):
    marker='formControlName="id_color"';at=s.index(marker);end=s.index('</select>',at)+len('</select>')
    s=s[:end]+'''<label>Colores adicionales de esta combinación<select class="fs-input" multiple formControlName="color_ids">@for(color of colores();track color.id_color){<option [ngValue]="color.id_color">{{color.nombre}}</option>}</select></label>'''+s[end:]
    s=s.replace('<label>Material','<label><input type="checkbox" formControlName="admite_cambio">Admite cambio según la política de siete días</label><label>Material',1)
    return s
edit('Parcial2_frontend-web/src/app/features/prendas/prenda-modal/prenda-modal.html',template)
edit('Parcial2_frontend-web/src/app/core/models/catalogo.model.ts',lambda s:s.replace('  id_color: number;','  color_ids?:number[];\n  id_color: number;').replace('  material?: string | null;','  admite_cambio?: boolean;\n  material?: string | null;'))
edit('Parcial2_frontend-web/src/app/app.routes.ts',lambda s:s.replace("'Cajero'","'Cajero (POS)'"))
