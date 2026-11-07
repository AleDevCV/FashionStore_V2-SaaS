const fs=require('node:fs'),path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
const ts=require(path.join(ROOT,'Parcial2_frontend-web/node_modules/typescript'));
const OUT=path.join(ROOT,'tmp/class-model');fs.mkdirSync(OUT,{recursive:true});
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
const files=walk(path.join(ROOT,'Parcial2_frontend-web/src/app')).filter(f=>f.endsWith('.ts')&&!f.endsWith('.spec.ts'));
const program=ts.createProgram(files,{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext,moduleResolution:ts.ModuleResolutionKind.Bundler,experimentalDecorators:true,skipLibCheck:true,noEmit:true});
const checker=program.getTypeChecker(),nodes=[],refs=[];
const short=t=>t.replace(/\s+/g,' ').trim();
const position=(sf,n)=>sf.getLineAndCharacterOfPosition(n.getStart(sf)).line+1;
const flags=n=>ts.getCombinedModifierFlags(n);
function visibility(n){const f=flags(n);return f&ts.ModifierFlags.Private?'-':f&ts.ModifierFlags.Protected?'#':'+';}
function typeOf(n){try{return short(n.type?n.type.getText():checker.typeToString(checker.getTypeAtLocation(n),n,ts.TypeFormatFlags.NoTruncation));}catch{return '';}}
function params(n){return (n.parameters||[]).map(p=>({name:p.name.getText(),type:typeOf(p),optional:!!p.questionToken||!!p.initializer,rest:!!p.dotDotDotToken}));}
function method(n,sf){let name=ts.isConstructorDeclaration(n)?'constructor':n.name?.getText()||'?';let ret='';try{ret=n.type?n.type.getText():ts.isConstructorDeclaration(n)?'':checker.typeToString(checker.getReturnTypeOfSignature(checker.getSignatureFromDeclaration(n)),n,ts.TypeFormatFlags.NoTruncation);}catch{}
 return {name,visibility:visibility(n),params:params(n),return:short(ret),static:!!(flags(n)&ts.ModifierFlags.Static),line:position(sf,n),kind:ts.isGetAccessor(n)?'getter':ts.isSetAccessor(n)?'setter':'method'};}
for(const file of files){
 const sf=program.getSourceFile(file),src=path.relative(ROOT,file).replaceAll('\\','/'),imports=[];
 for(const st of sf.statements)if(ts.isImportDeclaration(st)){
  const names=[];if(st.importClause?.name)names.push(st.importClause.name.text);
  const b=st.importClause?.namedBindings;if(b&&ts.isNamedImports(b))for(const e of b.elements)names.push(e.name.text);
  imports.push({path:st.moduleSpecifier.text,names});
 }
 const declarations=sf.statements.filter(n=>ts.isClassDeclaration(n)||ts.isInterfaceDeclaration(n)||ts.isEnumDeclaration(n)||ts.isTypeAliasDeclaration(n));
 for(const n of declarations){
  if(!n.name)continue;const name=n.name.text,id=src+'::'+name;
  const item={id,name,source:src,line:position(sf,n),end:sf.getLineAndCharacterOfPosition(n.end).line+1,language:'TypeScript',kind:ts.isInterfaceDeclaration(n)?'interface':ts.isEnumDeclaration(n)?'enum':ts.isTypeAliasDeclaration(n)?'type':'class',attributes:[],methods:[],bases:[],imports};
  for(const h of n.heritageClauses||[])for(const t of h.types)item.bases.push({name:t.getText(),kind:h.token===ts.SyntaxKind.ImplementsKeyword?'implements':'extends'});
  if(ts.isTypeAliasDeclaration(n)){
   if(ts.isTypeLiteralNode(n.type))for(const m of n.type.members){
    if(ts.isPropertySignature(m))item.attributes.push({name:m.name.getText(),type:typeOf(m),visibility:'+',optional:!!m.questionToken,static:false,line:position(sf,m)});
    if(ts.isMethodSignature(m))item.methods.push(method(m,sf));
   }
   else item.value_type=short(n.type.getText());
  }
  for(const m of n.members||[]){
   if(ts.isPropertyDeclaration(m)||ts.isPropertySignature(m))item.attributes.push({name:m.name.getText(),type:typeOf(m),visibility:visibility(m),optional:!!m.questionToken,static:!!(flags(m)&ts.ModifierFlags.Static),line:position(sf,m)});
   if(ts.isEnumMember(m))item.attributes.push({name:m.name.getText(),type:'',visibility:'+',static:true,line:position(sf,m)});
   if(ts.isConstructorDeclaration(m)||ts.isMethodDeclaration(m)||ts.isMethodSignature(m)||ts.isGetAccessor(m)||ts.isSetAccessor(m)){
    item.methods.push(method(m,sf));
    if(ts.isConstructorDeclaration(m))for(const p of m.parameters)if(flags(p)&(ts.ModifierFlags.Public|ts.ModifierFlags.Private|ts.ModifierFlags.Protected|ts.ModifierFlags.Readonly))item.attributes.push({name:p.name.getText(),type:typeOf(p),visibility:visibility(p),static:false,line:position(sf,p)});
   }
  }
  function references(node){if(ts.isIdentifier(node)){try{let symbol=checker.getSymbolAtLocation(node);if(symbol?.flags&ts.SymbolFlags.Alias)symbol=checker.getAliasedSymbol(symbol);for(const d of symbol?.declarations||[])if((ts.isClassDeclaration(d)||ts.isInterfaceDeclaration(d)||ts.isTypeAliasDeclaration(d)||ts.isEnumDeclaration(d))&&d.name){const target=path.relative(ROOT,d.getSourceFile().fileName).replaceAll('\\','/')+'::'+d.name.text;if(target!==id)refs.push({source:id,target,kind:'uses',file:src,line:position(sf,node)});}}catch{}}ts.forEachChild(node,references);}
  references(n);nodes.push(item);
 }
 const operations=sf.statements.filter(ts.isFunctionDeclaration).filter(n=>n.name).map(n=>({...method(n,sf),static:true}));
 for(const st of sf.statements)if(ts.isVariableStatement(st))for(const d of st.declarationList.declarations){
  if(d.initializer&&(ts.isArrowFunction(d.initializer)||ts.isFunctionExpression(d.initializer)))
   operations.push({...method(d.initializer,sf),name:d.name.getText(),static:true});
 }
 if(operations.length)nodes.push({id:src+'::$module',name:path.basename(file),source:src,line:1,end:sf.getLineAndCharacterOfPosition(sf.end).line+1,language:'TypeScript',kind:'module',attributes:[],methods:operations,bases:[],imports});
}
fs.writeFileSync(path.join(OUT,'typescript.json'),JSON.stringify({nodes,refs,files:files.map(f=>path.relative(ROOT,f).replaceAll('\\','/'))},null,2));
console.log('TypeScript:',nodes.length,'classifiers,',nodes.reduce((s,n)=>s+n.methods.length,0),'operations');
