# -*- coding: utf-8 -*-
"""
Script para generar docs/DOCUMENTACION PARCIAL 2/SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE_CONSOLIDADO.docx
a partir de SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE.docx y CAPITULO_V_CONSOLIDADO.md.
"""

import os
import re
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ORIGINAL_DOCX = r"c:\Examen si2 FASHIONSTORE\docs\DOCUMENTACION PARCIAL 2\SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE.docx"
TARGET_DOCX = r"c:\Examen si2 FASHIONSTORE\docs\DOCUMENTACION PARCIAL 2\SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE_CONSOLIDADO.docx"
MD_PATH = r"c:\Examen si2 FASHIONSTORE\docs\DOCUMENTACION PARCIAL 2\CAPITULO_V_CONSOLIDADO.md"

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m_name, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m_name}')
        node.set(qn('w:val'), str(val))
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), color_hex)
    tcPr.append(shd)

def set_table_borders(table):
    tblPr = table._tbl.tblPr
    tblBorders = OxmlElement('w:tblBorders')
    for b in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        border = OxmlElement(f'w:{b}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')  # 0.5 pt
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), 'B0B0B0')  # subtle gray
        tblBorders.append(border)
    tblPr.append(tblBorders)

def add_markdown_runs(paragraph, text, base_font_size=11, is_italic=False, is_mono=False):
    """Parsea negritas **texto** dentro de una cadena markdown y añade runs."""
    pattern = re.compile(r'(\*\*.*?\*\*)')
    tokens = pattern.split(text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            clean = token[2:-2]
            run = paragraph.add_run(clean)
            run.bold = True
        else:
            run = paragraph.add_run(token)
            if is_italic:
                run.italic = True
        
        run.font.name = 'Consolas' if is_mono else 'Times New Roman'
        run.font.size = Pt(base_font_size)
        run.font.color.rgb = RGBColor(0, 0, 0)

def main():
    print(f"Cargando documento original: {ORIGINAL_DOCX}")
    doc = docx.Document(ORIGINAL_DOCX)
    body = doc._body._element

    # 1. Localizar Capítulo V y Capítulo VI
    p_v = None
    p_vi = None
    for p in doc.paragraphs:
        t = p.text.upper()
        if 'CAPÍTULO V.' in t and 'RESULTADOS' in t and not any(c.isdigit() for c in p.text.strip()[-3:]):
            p_v = p
        elif 'CAPÍTULO VI.' in t and 'CONCLUSIONES' in t and not any(c.isdigit() for c in p.text.strip()[-3:]):
            p_vi = p
            break

    if not p_v or not p_vi:
        raise RuntimeError("No se pudieron localizar los límites del Capítulo V y VI")

    idx_v = body.index(p_v._p)
    idx_vi = body.index(p_vi._p)
    print(f"Capítulo V inicia en body[{idx_v}], Capítulo VI inicia en body[{idx_vi}]")

    # 2. Eliminar contenido anterior entre p_v y p_vi
    elements_to_remove = body[idx_v + 1 : idx_vi]
    print(f"Eliminando {len(elements_to_remove)} elementos previos de Capítulo V...")
    for elem in elements_to_remove:
        body.remove(elem)

    # 3. Leer y parsear CAPITULO_V_CONSOLIDADO.md
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md_text = f.read()

    lines = md_text.split('\n')
    print(f"Procesando {len(lines)} líneas de Markdown consolidado...")

    # El encabezado "CAPÍTULO V. PRUEBAS Y RESULTADOS" ya está en p_v.
    # Omitimos el primer título si aparece en el markdown.
    
    i = 0
    in_code_block = False
    code_block_lines = []

    while i < len(lines):
        line = lines[i].rstrip()
        
        # Bloques de código ```
        if line.startswith('```'):
            if in_code_block:
                # Cerrar bloque de código
                in_code_block = False
                # Crear tabla o caja de código
                tbl = doc.add_table(rows=1, cols=1)
                tbl.autofit = False
                set_table_borders(tbl)
                cell = tbl.cell(0, 0)
                set_cell_shading(cell, 'F7F7F7')
                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                cp = cell.paragraphs[0]
                cp.paragraph_format.space_before = Pt(0)
                cp.paragraph_format.space_after = Pt(0)
                cp.paragraph_format.line_spacing = 1.0
                for c_line in code_block_lines:
                    run = cp.add_run(c_line + '\n')
                    run.font.name = 'Consolas'
                    run.font.size = Pt(8.5)
                    run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
                p_vi._p.addprevious(tbl._tbl)
                code_block_lines = []
            else:
                in_code_block = True
                code_block_lines = []
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Líneas vacías o separadores
        if not line.strip() or line.strip() == '---':
            i += 1
            continue

        # Omitir el título de nivel 1 si es "CAPÍTULO V..."
        if line.startswith('# '):
            # Agregar el párrafo introductorio debajo de p_v si la siguiente línea no es título
            i += 1
            continue

        # Título Nivel 2: ## 5.x. ...
        if line.startswith('## '):
            heading_text = line[3:].strip()
            p = doc.add_paragraph(heading_text, style='Heading 2')
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            p_vi._p.addprevious(p._p)
            i += 1
            continue

        # Título Nivel 3: ### 5.x.x. ...
        if line.startswith('### '):
            heading_text = line[4:].strip()
            p = doc.add_paragraph(heading_text, style='Heading 3')
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            p_vi._p.addprevious(p._p)
            i += 1
            continue

        # Blockquote / Alert: > [!NOTE], > ...
        if line.startswith('>'):
            clean_bq = line.lstrip('>').strip()
            # Si hay líneas siguientes que también son bq, agruparlas
            bq_lines = [clean_bq]
            while i + 1 < len(lines) and lines[i+1].startswith('>'):
                i += 1
                bq_lines.append(lines[i].lstrip('>').strip())
            
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.35)
            p.paragraph_format.right_indent = Inches(0.2)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            
            full_bq_text = " ".join(bq_lines)
            add_markdown_runs(p, full_bq_text, base_font_size=10.5, is_italic=True)
            p_vi._p.addprevious(p._p)
            i += 1
            continue

        # Tablas Markdown: | ... | ... |
        if line.startswith('|') and '|' in line[1:]:
            table_lines = [line]
            while i + 1 < len(lines) and lines[i+1].startswith('|'):
                i += 1
                table_lines.append(lines[i].rstrip())
            
            # Parsear filas y columnas
            rows_data = []
            for tl in table_lines:
                # Omitir fila separadora |---|---|
                parts = [c.strip() for c in tl.split('|')[1:-1]]
                if all(set(c).issubset({'-', ':', ' '}) for c in parts):
                    continue
                rows_data.append(parts)

            if rows_data:
                num_rows = len(rows_data)
                num_cols = max(len(r) for r in rows_data)
                tbl = doc.add_table(rows=num_rows, cols=num_cols)
                tbl.autofit = False
                set_table_borders(tbl)

                # Ancho total aproximado: 9350 dxa (~6.5 pulgadas)
                TOTAL_DXA = 9350
                col_width_dxa = int(TOTAL_DXA / num_cols)

                for r_idx, row in enumerate(tbl.rows):
                    trPr = row._tr.get_or_add_trPr()
                    cantSplit = OxmlElement('w:cantSplit')
                    trPr.append(cantSplit)
                    
                    is_header = (r_idx == 0)
                    if is_header:
                        tblHeader = OxmlElement('w:tblHeader')
                        trPr.append(tblHeader)

                    row_cells_data = rows_data[r_idx]
                    for c_idx in range(num_cols):
                        cell = row.cells[c_idx]
                        cell.width = Inches(col_width_dxa / 1440.0)
                        set_cell_margins(cell, top=70, bottom=70, left=100, right=100)

                        if is_header:
                            set_cell_shading(cell, 'EAEAEA')

                        val = row_cells_data[c_idx] if c_idx < len(row_cells_data) else ""
                        cp = cell.paragraphs[0]
                        cp.paragraph_format.space_before = Pt(0)
                        cp.paragraph_format.space_after = Pt(0)
                        cp.paragraph_format.line_spacing = 1.05

                        # Elegir tamaño según densidad
                        cell_font_size = 9.0 if num_cols >= 6 else (9.5 if num_cols >= 4 else 10.0)
                        add_markdown_runs(cp, val, base_font_size=cell_font_size)
                        if is_header:
                            for r in cp.runs:
                                r.bold = True

                p_vi._p.addprevious(tbl._tbl)
            i += 1
            continue

        # Lista desordenada o numerada
        if line.startswith('- ') or line.startswith('* ') or re.match(r'^\d+\.\s', line):
            is_num = bool(re.match(r'^\d+\.\s', line))
            clean_item = re.sub(r'^\d+\.\s', '', line) if is_num else line[2:].strip()
            
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.15
            
            prefix = f"{line.split()[0]} " if is_num else "• "
            r_pre = p.add_run(prefix)
            r_pre.bold = True
            r_pre.font.name = 'Times New Roman'
            r_pre.font.size = Pt(11)
            
            add_markdown_runs(p, clean_item, base_font_size=11)
            p_vi._p.addprevious(p._p)
            i += 1
            continue

        # Párrafo normal
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_markdown_runs(p, line, base_font_size=11.5)
        p_vi._p.addprevious(p._p)
        i += 1

    # 4. Configurar actualización automática de campos (TOC) en settings.xml
    try:
        settings = doc.settings._element
        updateFields = OxmlElement('w:updateFields')
        updateFields.set(qn('w:val'), 'true')
        settings.append(updateFields)
        print("Configuración w:updateFields agregada exitosamente a word/settings.xml")
    except Exception as e:
        print(f"Nota sobre updateFields: {e}")

    # 5. Guardar en el nuevo documento Word consolidado
    print(f"Guardando documento consolidado en: {TARGET_DOCX}")
    doc.save(TARGET_DOCX)
    print(f"Documento guardado con éxito. Tamaño: {os.path.getsize(TARGET_DOCX)} bytes")

if __name__ == '__main__':
    main()

