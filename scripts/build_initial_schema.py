"""Extrae DDL sin los DROP ni datos personales de la semilla anterior."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
base=(ROOT/'Parcial2_backend/database/db_scheme.sql').read_text(encoding='utf-8-sig')
base=base[:base.index('INSERT INTO rol (id_rol')]
base='\n'.join(line for line in base.splitlines() if not line.strip().startswith('DROP TABLE'))
out=ROOT/'Parcial2_backend/database/migrations';out.mkdir(parents=True,exist_ok=True)
(out/'001_baseline.sql').write_text('-- Solo inicialización de una base nueva. No ejecuta DROP ni importa usuarios P1.\n'+base,encoding='utf-8')
print('DDL inicial sin semillas personales generado.')
