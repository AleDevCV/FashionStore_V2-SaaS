import 'dart:convert';
import 'dart:io';
import 'package:analyzer/dart/analysis/utilities.dart';
import 'package:analyzer/dart/ast/ast.dart';
import 'package:analyzer/dart/ast/visitor.dart';

String compact(String s)=>s.replaceAll(RegExp(r'\s+'),' ').trim();
String relative(String p)=>p.replaceAll('\\','/').replaceFirst(Directory.current.path.replaceAll('\\','/')+'/','');
String vis(String n)=>n.startsWith('_')?'-':'+';
class TypeVisitor extends RecursiveAstVisitor<void>{
 final Set<String> values={};
 @override void visitNamedType(NamedType n){values.add(n.toSource());super.visitNamedType(n);}
}
void main(){
 final nodes=<Map<String,dynamic>>[];final refs=<Map<String,dynamic>>[];final files=<String>[];
 for(final entity in Directory('Parcial2_mobile/lib').listSync(recursive:true)){
  if(entity is! File||!entity.path.endsWith('.dart'))continue;
  final src=relative(entity.absolute.path);files.add(src);
  final parsed=parseString(content:entity.readAsStringSync(),path:entity.path,throwIfDiagnostics:false);
  final unit=parsed.unit;
  if(parsed.errors.any((e)=>e.errorCode.type.name=='SYNTACTIC_ERROR'))throw StateError('Syntax errors: $src');
  int line(AstNode n)=>parsed.lineInfo.getLocation(n.offset).lineNumber;
  final imports=unit.directives.whereType<ImportDirective>().map((d)=>{'path':d.uri.stringValue,'prefix':d.prefix?.name}).toList();
  Map<String,dynamic> operation(String name,FormalParameterList? params,String? result,int at,{bool isStatic=false,String kind='method'})=>{
    'name':name,'visibility':vis(name.split('.').last),'raw_params':compact(params?.toSource()??'()'),'return':compact(result??''),'static':isStatic,'line':at,'kind':kind
  };
  final top=<Map<String,dynamic>>[];
  for(final decl in unit.declarations){
   if(decl is FunctionDeclaration){top.add(operation(decl.name.lexeme,decl.functionExpression.parameters,decl.returnType?.toSource(),line(decl),isStatic:true));continue;}
   if(decl is! ClassDeclaration&&decl is! EnumDeclaration)continue;
   final dynamic d=decl;final name=d.name.lexeme as String;
   final members=decl is ClassDeclaration?decl.members:(decl as EnumDeclaration).members;
   final attributes=<Map<String,dynamic>>[];final methods=<Map<String,dynamic>>[];final bases=<Map<String,String>>[];
   if(decl is ClassDeclaration){
    if(decl.extendsClause!=null)bases.add({'name':decl.extendsClause!.superclass.toSource(),'kind':'extends'});
    for(final t in decl.implementsClause?.interfaces??<NamedType>[])bases.add({'name':t.toSource(),'kind':'implements'});
    for(final t in decl.withClause?.mixinTypes??<NamedType>[])bases.add({'name':t.toSource(),'kind':'mixin'});
   }
   for(final m in members){
    if(m is FieldDeclaration){
     for(final v in m.fields.variables)attributes.add({'name':v.name.lexeme,'type':compact(m.fields.type?.toSource()??''),'visibility':vis(v.name.lexeme),'static':m.isStatic,'line':line(v)});
    }else if(m is MethodDeclaration){
     methods.add(operation(m.name.lexeme,m.parameters,m.returnType?.toSource(),line(m),isStatic:m.isStatic,kind:m.isGetter?'getter':m.isSetter?'setter':'method'));
    }else if(m is ConstructorDeclaration){
     methods.add(operation(name+(m.name==null?'':'.'+m.name!.lexeme),m.parameters,null,line(m),isStatic:m.factoryKeyword!=null,kind:'constructor'));
    }
   }
   if(decl is EnumDeclaration)for(final constant in decl.constants)attributes.add({'name':constant.name.lexeme,'type':'','visibility':'+','static':true,'line':line(constant)});
   final collector=TypeVisitor();decl.accept(collector);
   nodes.add({'id':'$src::$name','name':name,'source':src,'line':line(decl),'end':parsed.lineInfo.getLocation(decl.end).lineNumber,'language':'Dart','kind':decl is EnumDeclaration?'enum':'class','attributes':attributes,'methods':methods,'bases':bases,'imports':imports,'type_refs':collector.values.toList()});
  }
  if(top.isNotEmpty)nodes.add({'id':src+'::module','name':entity.uri.pathSegments.last,'source':src,'line':1,'end':parsed.lineInfo.getLocation(unit.end).lineNumber,'language':'Dart','kind':'module','attributes':<dynamic>[],'methods':top,'bases':<dynamic>[],'imports':imports});
 }
 Directory('tmp/class-model').createSync(recursive:true);
 File('tmp/class-model/dart.json').writeAsStringSync(const JsonEncoder.withIndent('  ').convert({'nodes':nodes,'refs':refs,'files':files}));
 print('Dart: '+nodes.length.toString()+' classifiers; '+nodes.fold<int>(0,(s,n)=>s+(n['methods'] as List).length).toString()+' operations');
}
