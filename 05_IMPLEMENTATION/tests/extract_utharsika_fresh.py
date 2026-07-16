"""
Fresh full-data extraction of the Utharsika sheet in the new single-tab
workbook. Read-only. Finds the true data-row range and any total row
by scanning the actual rows (not assuming a specific row number).
"""
import zipfile
import xml.etree.ElementTree as ET
import json
import os

ns = {'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
XLSX = os.path.join(os.path.dirname(__file__), "..", "..", "02_SOURCE", "user_provided",
                     "2026-07-10_utharsika_june_july_kpi_reference_b01.xlsx")

z = zipfile.ZipFile(XLSX)
sst_root = ET.fromstring(z.read('xl/sharedStrings.xml'))
shared_strings = []
for si in sst_root.findall('a:si', ns):
    texts = si.findall('.//a:t', ns)
    shared_strings.append(''.join((t.text or '') for t in texts))

sheet_xml = z.read('xl/worksheets/sheet1.xml')
root = ET.fromstring(sheet_xml)
sheetdata = root.find('a:sheetData', ns)
rows = sheetdata.findall('a:row', ns)

def cell_value(c):
    t = c.get('t')
    v = c.find('a:v', ns)
    is_ = c.find('a:is', ns)
    if is_ is not None:
        return ''.join((x.text or '') for x in is_.findall('.//a:t', ns))
    if v is None:
        return None
    if t == 's':
        idx = int(v.text)
        return shared_strings[idx] if idx < len(shared_strings) else None
    return v.text

def cell_formula(c):
    f = c.find('a:f', ns)
    return f.text if f is not None else None

records = []
first_data_row = None
last_data_row = None
non_asin_rows_with_values = []

for row in rows:
    rnum = int(row.get('r'))
    if rnum <= 2:
        continue
    cells = {}
    formulas = {}
    for c in row.findall('a:c', ns):
        ref = c.get('r')
        col = ''.join(ch for ch in ref if ch.isalpha())
        cells[col] = cell_value(c)
        formulas[col] = cell_formula(c)

    asin = cells.get('A')
    has_any_value = any(v not in (None, '') for v in cells.values())

    if asin in (None, ''):
        if has_any_value:
            non_asin_rows_with_values.append({'row': rnum, 'cells': cells, 'formulas_present': {k: bool(v) for k, v in formulas.items() if v}})
        continue

    if first_data_row is None:
        first_data_row = rnum
    last_data_row = rnum

    records.append({
        'row': rnum,
        'asin': asin.strip() if isinstance(asin, str) else asin,
        'account': cells.get('B'),
        'sku': cells.get('C'),
        'mapped_sku': cells.get('D'),
        'K_june_sales_2025': cells.get('K'),
        'L_june_orders_2025': cells.get('L'),
        'M_june_sales_2026': cells.get('M'),
        'N_june_orders_2026': cells.get('N'),
        'O_july_sales_2025': cells.get('O'),
        'P_july_orders_2025': cells.get('P'),
        'Q_july_sales_2026': cells.get('Q'),
        'R_july_orders_2026': cells.get('R'),
    })

print('FIRST DATA ROW:', first_data_row)
print('LAST DATA ROW:', last_data_row)
print('TOTAL DATA RECORDS (rows with non-blank ASIN):', len(records))
print('\nNON-ASIN ROWS WITH ANY VALUES (candidate total/summary rows):')
for r in non_asin_rows_with_values:
    print(' ', r)

# check for rows beyond last_data_row that still have any content at all
max_row_overall = max(int(row.get('r')) for row in rows)
print('\nMAX ROW NUMBER IN SHEET (any content):', max_row_overall)
rows_after_last_data = [row for row in rows if int(row.get('r')) > (last_data_row or 0)]
print('ROWS AFTER LAST DATA ROW:', len(rows_after_last_data))
for row in rows_after_last_data[:10]:
    rnum = row.get('r')
    cells = []
    for c in row.findall('a:c', ns):
        ref = c.get('r')
        val = cell_value(c)
        if val not in (None, ''):
            cells.append(f'{ref}={val!r}')
    if cells:
        print(f'  ROW {rnum}:', ' | '.join(cells))

out_path = os.path.join(os.path.dirname(__file__), "..", "state", "utharsika_fresh_records.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump({'first_data_row': first_data_row, 'last_data_row': last_data_row,
               'records': records, 'non_asin_rows_with_values': non_asin_rows_with_values}, f)
print(f'\nSaved {len(records)} records to {out_path}')
