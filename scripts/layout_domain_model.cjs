// Genera una sola vista general con clases UML nativas y asociaciones editables.
const fs=require('node:fs/promises');
const path=require('node:path');
const {instance}=require('@viz-js/viz');
const sharp=require('sharp');
const ROOT=path.resolve(__dirname,'..');
const OUT=path.join(ROOT,'docs','modelo_dominio');
const TMP=path.join(ROOT,'tmp','domain-layout');
const xml=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll('\n','&#xa;');
const q=s=>JSON.stringify(String(s));
const COLORS={organizacion:'#e4edf8',identidad:'#e9edf5',catalogo:'#e4f1e9',asistencia:'#e4f1e9',inventario:'#e6f0ef',abastecimiento:'#f4eddf',compra_digital:'#e9edf9',pagos:'#f4e9df',ventas:'#e8edf8',reservas:'#edf0df',cambios:'#f6e7e5',offline:'#e8eef5',sincronizacion:'#e8eef5',reportes:'#eee8f6',analitica:'#eee8f6',trazabilidad:'#e9edf0'};

function attrs(obj){return Object.entries(obj).map(([k,v])=>k+'='+q(v)).join(',');}
function parsePoint(value){return value.split(',').map(Number);}
function midpoint(points){
 let remaining=points.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p[0]-points[i][0],p[1]-points[i][1]),0)/2;
 for(let i=1;i<points.length;i++){
  const a=points[i-1],b=points[i],len=Math.hypot(b[0]-a[0],b[1]-a[1]);
  if(remaining<=len){const f=len?remaining/len:0;return[a[0]+f*(b[0]-a[0]),a[1]+f*(b[1]-a[1])];}remaining-=len;
 }return points[0];
}
function sampleSpline(points){
 if(points.length<4)return points;
 const output=[points[0]];
 for(let i=1;i+2<points.length;i+=3){
  const [a,b,c,d]=[points[i-1],points[i],points[i+1],points[i+2]];
  for(let j=1;j<=5;j++){const t=j/5,u=1-t;output.push([u*u*u*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t*t*t*d[0],u*u*u*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t*t*t*d[1]]);}
 }return output;
}

(async()=>{
 await fs.mkdir(TMP,{recursive:true});
 const model=JSON.parse(await fs.readFile(path.join(OUT,'modelo_dominio.json'),'utf8'));
 const dot=['digraph Dominio {','graph [rankdir=LR,ranksep=1.15,nodesep=0.55,fontsize=18,fontname="Arial",splines=spline,overlap=false,outputorder=edgesfirst,bgcolor="white",pad=0.5];','node [shape=plain,fontname="Arial",fontsize=17];','edge [fontname="Arial",fontsize=13,fontcolor="#33455c",color="#75879a",arrowsize=0.8,labeldistance=2.1,labelangle=23,penwidth=1.2];'];
 for(const group of [...new Set(model.clases.map(n=>n.grupo))]){
  for(const n of model.clases.filter(n=>n.grupo===group)){
   const table='<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="11" COLOR="#536b83"><TR><TD BGCOLOR="'+COLORS[group]+'"><FONT POINT-SIZE="18"><B>'+xml(n.nombre)+'</B></FONT></TD></TR><TR><TD ALIGN="LEFT"><FONT POINT-SIZE="16">'+n.atributos.map(xml).join('<BR ALIGN="LEFT"/>')+'<BR ALIGN="LEFT"/></FONT></TD></TR></TABLE>';
   dot.push(n.id+' [label=<'+table+'>];');
  }
 }
 for(const e of model.relaciones){
  const config={id:e.id,label:e.nombre,taillabel:e.multiplicidad_origen,headlabel:e.multiplicidad_destino,dir:e.composicion?'both':'none',arrowhead:'none',arrowtail:e.composicion?'diamond':'none',constraint:'true',weight:e.ordenar?'5':'1'};
  dot.push(e.origen+' -> '+e.destino+' ['+attrs(config)+'];');
 }
 dot.push('}');const source=dot.join('\n');
 await fs.writeFile(path.join(TMP,'dominio.dot'),source);
 const viz=await instance();
 const result=viz.renderFormats(source,['json','svg'],{engine:'dot'});
 if(result.status!=='success')throw new Error(JSON.stringify(result.errors));
 const layout=JSON.parse(result.output.json);
 await fs.writeFile(path.join(TMP,'layout.json'),JSON.stringify(layout,null,2));
 const svg=result.output.svg.replace(/<!--[\s\S]*?-->/g,'').replace(/<!DOCTYPE[\s\S]*?>/,'');
 await fs.writeFile(path.join(OUT,'FashionStore_Modelo_Dominio_General.svg'),svg);
 const bounds=layout.bb.split(',').map(Number);const H=bounds[3],W=bounds[2],margin=60;
 const nodeMap=new Map();
 for(const n of layout.objects||[]){if(!model.clases.some(c=>c.id===n.name))continue;const p=parsePoint(n.pos),w=Number(n.width)*72,h=Number(n.height)*72;nodeMap.set(n.name,{x:p[0]-w/2+margin,y:H-p[1]-h/2+margin,w,h});}
 if(nodeMap.size!==model.clases.length)throw new Error('Faltan conceptos en el layout.');
 const transform=p=>[p[0]+margin,H-p[1]+margin];
 const num=n=>Number(n.toFixed(3));
 let parts=['<?xml version="1.0" encoding="UTF-8"?>','<mxfile host="app.diagrams.net" version="29.0.0"><diagram id="dominio-general" name="Modelo de dominio general"><mxGraphModel grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="0" page="1" pageScale="1" pageWidth="'+Math.ceil(W+margin*2)+'" pageHeight="'+Math.ceil(H+margin*2)+'" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>'];
 for(const e of model.relaciones){
  const placed=layout.edges.find(x=>x.id===e.id);if(!placed)throw new Error('Relación no encontrada '+e.id);
  const spline=placed._draw_?.find(d=>d.op==='b')?.points;
  if(!spline)throw new Error('No se pudo recuperar trayectoria '+e.id);
  const points=sampleSpline(spline).map(transform),first=points[0],last=points.at(-1),s=nodeMap.get(e.origen),t=nodeMap.get(e.destino);
  const clamp=v=>Math.max(0,Math.min(1,v));
  const ports='exitX='+num(clamp((first[0]-s.x)/s.w))+';exitY='+num(clamp((first[1]-s.y)/s.h))+';exitPerimeter=0;entryX='+num(clamp((last[0]-t.x)/t.w))+';entryY='+num(clamp((last[1]-t.y)/t.h))+';entryPerimeter=0;';
  const st='edgeStyle=none;curved=0;rounded=0;html=0;endArrow=none;startArrow='+(e.composicion?'diamond':'none')+';startFill=1;strokeColor=#75879a;strokeWidth=1.2;fontColor=#33455c;fontSize=13;labelBackgroundColor=#ffffff;'+ports;
  const mid=midpoint(points),lp=placed.lp?transform(parsePoint(placed.lp)):mid;
  parts.push('<mxCell id="'+e.id+'" value="'+xml(e.nombre)+'" style="'+st+'" edge="1" parent="1" source="'+e.origen+'" target="'+e.destino+'"><mxGeometry x="0" y="0" relative="1" as="geometry"><Array as="points">'+points.slice(1,-1).map(p=>'<mxPoint x="'+num(p[0])+'" y="'+num(p[1])+'"/>').join('')+'</Array><mxPoint as="offset" x="'+num(lp[0]-mid[0])+'" y="'+num(lp[1]-mid[1])+'"/></mxGeometry></mxCell>');
  for(const [kind,value,anchor,pos] of [['tail',e.multiplicidad_origen,first,placed.tail_lp],['head',e.multiplicidad_destino,last,placed.head_lp]]){
   const p=pos?transform(parsePoint(pos)):[anchor[0]+10,anchor[1]-15];
   const style='edgeLabel;html=0;align=center;verticalAlign=middle;resizable=0;whiteSpace=wrap;fontSize=13;fontColor=#23374d;labelBackgroundColor=#ffffff;';
   parts.push('<mxCell id="'+e.id+'_'+kind+'" value="'+xml(value)+'" style="'+style+'" vertex="1" connectable="0" parent="'+e.id+'"><mxGeometry x="'+(kind==='tail'?-1:1)+'" y="0" width="54" height="24" relative="1" as="geometry"><mxPoint as="offset" x="'+num(p[0]-anchor[0]-27)+'" y="'+num(p[1]-anchor[1]-12)+'"/></mxGeometry></mxCell>');
  }
 }
 for(const n of model.clases){
  const p=nodeMap.get(n.id),startSize=42;
  const style='swimlane;horizontal=1;startSize='+startSize+';rounded=0;html=0;whiteSpace=wrap;collapsible=0;recursiveResize=0;fontStyle=1;fontSize=18;align=center;verticalAlign=middle;fillColor='+COLORS[n.grupo]+';swimlaneFillColor=#ffffff;strokeColor=#536b83;strokeWidth=1.2;';
  parts.push('<mxCell id="'+n.id+'" value="'+xml(n.nombre)+'" style="'+style+'" vertex="1" parent="1"><mxGeometry x="'+num(p.x)+'" y="'+num(p.y)+'" width="'+num(p.w)+'" height="'+num(p.h)+'" as="geometry"/></mxCell>');
  parts.push('<mxCell id="'+n.id+'_atributos" value="'+xml(n.atributos.join('\n'))+'" style="text;html=0;whiteSpace=wrap;align=left;verticalAlign=top;spacingTop=9;spacingLeft=11;fontSize=16;fontStyle=0;fontColor=#26364a;fillColor=none;strokeColor=none;overflow=hidden;" vertex="1" connectable="0" parent="'+n.id+'"><mxGeometry x="0" y="'+startSize+'" width="'+num(p.w)+'" height="'+num(p.h-startSize)+'" as="geometry"/></mxCell>');
 }
 parts.push('</root></mxGraphModel></diagram></mxfile>');
 await fs.writeFile(path.join(OUT,'FashionStore_Modelo_Dominio_General.drawio'),parts.join('\n'));
 await sharp(Buffer.from(svg),{density:72,limitInputPixels:false}).resize({width:3200}).png().toFile(path.join(OUT,'FashionStore_Modelo_Dominio_General.png'));
 await fs.writeFile(path.join(TMP,'dimensiones.json'),JSON.stringify({width:W,height:H,clases:model.clases.length,relaciones:model.relaciones.length,warnings:result.errors},null,2));
 console.log(JSON.stringify({clases:model.clases.length,relaciones:model.relaciones.length,ancho:Math.ceil(W+margin*2),alto:Math.ceil(H+margin*2),vistas:1,anotaciones:0}));
})().catch(error=>{console.error('No se pudo completar el modelo: '+error.message.slice(0,500));process.exitCode=1;});
