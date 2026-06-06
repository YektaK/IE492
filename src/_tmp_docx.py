import docx
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

doc = docx.Document(r'D:\IE492\docs\Bitirme Projesi son güncel 1.docx')

print("=== ALL TABLES ===", flush=True)
for ti, table in enumerate(doc.tables):
    print(f'\n--- Table {ti} ({len(table.rows)}x{len(table.columns)}) ---', flush=True)
    for ri, row in enumerate(table.rows):
        cells = [c.text.strip() for c in row.cells]
        print(f'  R{ri}: {cells}', flush=True)
        if ri > 20:
            print('  ... (truncated)', flush=True)
            break
