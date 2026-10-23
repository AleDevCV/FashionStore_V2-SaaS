"""Importación selectiva e idempotente; nunca sobrescribe fuentes existentes."""
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(r'C:\SISTEMAS DE INFORMACION 2')
SKIP={'.git','node_modules','venv','.venv','__pycache__','.dart_tool','.angular','build','dist','.idea','screenshots','tests','logs'}
CHOICES={
 'fashionstore-backend':('Parcial2_backend',['app','database/db_scheme.sql','database/migration_bloque3.sql','requirements.txt']),
 'fashionstore-web':('Parcial2_frontend-web',['src','public','angular.json','package.json','package-lock.json','tsconfig.json','tsconfig.app.json','tsconfig.spec.json']),
 'fashionstore-mobile':('Parcial2_mobile',['lib','android','assets','pubspec.yaml','pubspec.lock','analysis_options.yaml','.metadata']),
}

def main():
    copied=0
    for origin,(destination,names) in CHOICES.items():
        for name in names:
            src=SOURCE/origin/name
            if not src.exists():continue
            files=src.rglob('*') if src.is_dir() else [src]
            for item in files:
                if not item.is_file():continue
                rel=item.relative_to(SOURCE/origin)
                if any(x in SKIP for x in rel.parts) or item.name.startswith('.env') or item.suffix in {'.pyc','.log','.jks','.keystore'} or item.name in {'local.properties','key.properties'}:continue
                if 'comprobantes' in rel.parts and item.suffix.lower()=='.pdf':continue
                target=ROOT/destination/rel
                if target.exists():continue
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(item,target);copied+=1
    print(f'{copied} archivos incorporados sin modificar el origen ni copiar sus .git/.env.')

if __name__=='__main__':main()
