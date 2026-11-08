import docx

doc_path = r'c:\Examen si2 FASHIONSTORE\docs\DOCUMENTACION PARCIAL 2\SEGUNDO_EXAMEN_PARCIAL-FASHIONSTORE.docx'
doc = docx.Document(doc_path)

print(f'Total paragraphs in doc: {len(doc.paragraphs)}')
print(f'Total tables in doc:     {len(doc.tables)}')

p_v_idx = -1
p_vi_idx = -1

for i, p in enumerate(doc.paragraphs):
    t = p.text.strip().upper()
    if 'CAPÍTULO V.' in t and 'RESULTADOS' in t:
        if not any(c.isdigit() for c in t[-3:]):
            p_v_idx = i
            print(f'Found Chapter V heading at paragraph {i}: "{p.text.strip()}"')
    elif 'CAPÍTULO VI.' in t and 'CONCLUSIONES' in t:
        if not any(c.isdigit() for c in t[-3:]):
            p_vi_idx = i
            print(f'Found Chapter VI heading at paragraph {i}: "{p.text.strip()}"')
            break

print(f'Range of Chapter V in paragraphs: {p_v_idx} to {p_vi_idx}')
for i in range(p_v_idx, p_vi_idx + 1):
    print(f'p[{i}] (style={doc.paragraphs[i].style.name}): {doc.paragraphs[i].text[:80]}')

# Check tables between Chapter V and Chapter VI
# Note that in python-docx, doc.tables is a separate list, but each table has an underlying XML element <w:tbl>
# Let's see which tables are inside Chapter V in the document body XML
body = doc._body._element
p_v_elem = doc.paragraphs[p_v_idx]._p
p_vi_elem = doc.paragraphs[p_vi_idx]._p

found_v = False
tbl_count = 0
p_count = 0
for child in body:
    if child == p_v_elem:
        found_v = True
    elif child == p_vi_elem:
        found_v = False
        break
    elif found_v:
        if child.tag.endswith('tbl'):
            tbl_count += 1
        elif child.tag.endswith('p'):
            p_count += 1

print(f'Elements between Chapter V and Chapter VI: {p_count} paragraphs, {tbl_count} tables')

