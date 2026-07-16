"""
Fresh, from-scratch inspection of the NEW single-tab workbook:
02_SOURCE\\user_provided\\2026-07-10_utharsika_june_july_kpi_reference_b01.xlsx

Read-only. Does not modify the workbook. Reports header structure, merged
cells, formulas (to prove column meaning), data-row range, and any
total row - all from this file's own content, not from any prior
session's assumptions.
"""
import zipfile
import xml.etree.ElementTree as ET
import json
import os

ns = {'a': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
XLSX = os.path.join(os.path.dirname(__file__), "..", "..", "02_SOURCE", "user_provided",
                     "2026-07-10_utharsika_june_july_kpi_reference_b01.xlsx")

z = zipfile.ZipFile(XLSX)

# Confirm sheet count/name again from inside this script (not reused from shell)
wb_root = ET.fromstring(z.read('xl/workbook.xml'))
sheets = wb_root.find('a:sheets', ns)
sheet_list = [(s.get('name'), s.get('sheetId')) for s in sheets.findall('a:sheet', ns)]
print("SHEETS IN WORKBOOK:", sheet_list)
assert len(sheet_list) == 1, f"Expected exactly 1 sheet, found {len(sheet_list)}"
assert sheet_list[0][0] == "Utharsika", f"Expected sheet named 'Utharsika', found '{sheet_list[0][0]}'"

sst_root = ET.fromstring(z.read('xl/sharedStrings.xml'))
shared_strings = []
for si in sst_root.findall('a:si', ns):
    texts = si.findall('.//a:t', ns)
    shared_strings.append(''.join((t.text or '') for t in texts))

sheet_xml = z.read('xl/worksheets/sheet1.xml')
root = ET.fromstring(sheet_xml)

dim = root.find('a:dimension', ns)
print('DIMENSION:', dim.get('ref') if dim is not None else 'none')

sheet_pr = root.find('a:sheetPr', ns)
print('SHEET PR (tab color/filter mode if any):', ET.tostring(sheet_pr, encoding='unicode') if sheet_pr is not None else 'none')

auto_filter = root.find('a:autoFilter', ns)
print('AUTOFILTER:', auto_filter.get('ref') if auto_filter is not None else 'none')

merges = root.find('a:mergeCells', ns)
merge_list = []
if merges is not None:
    print('MERGE COUNT:', merges.get('count'))
    for mc in merges.findall('a:mergeCell', ns):
        ref = mc.get('ref')
        merge_list.append(ref)
        first = ref.split(':')[0]
        row_digits = ''.join(ch for ch in first if ch.isdigit())
        if row_digits and int(row_digits) <= 6:
            print('  MERGE (header area):', ref)

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

sheetdata = root.find('a:sheetData', ns)
rows = sheetdata.findall('a:row', ns)
print('TOTAL <row> ELEMENTS:', len(rows))

# Check for hidden rows
hidden_rows = [row.get('r') for row in rows if row.get('hidden') == '1']
print('HIDDEN ROWS:', hidden_rows[:20], '...' if len(hidden_rows) > 20 else '', f'(count={len(hidden_rows)})')

# Print first 6 rows fully (values)
print("\n--- FIRST 6 ROWS (values) ---")
for row in rows[:6]:
    r = row.get('r')
    cells = []
    for c in row.findall('a:c', ns):
        ref = c.get('r')
        val = cell_value(c)
        if val not in (None, ''):
            cells.append(f'{ref}={val!r}')
    print(f'ROW {r}:', ' | '.join(cells))

# Print formulas for row 3 (first data row) across all columns present
print("\n--- ROW 3 FORMULAS (all columns) ---")
row3 = next((row for row in rows if row.get('r') == '3'), None)
if row3 is not None:
    for c in row3.findall('a:c', ns):
        ref = c.get('r')
        f = cell_formula(c)
        v = cell_value(c)
        if f or v:
            print(f'{ref}: formula={f!r} value={v!r}')

with open(os.path.join(os.path.dirname(__file__), "..", "state", "utharsika_fresh_meta.json"), "w") as f:
    json.dump({"sheets": sheet_list, "dimension": dim.get('ref') if dim is not None else None,
               "merge_count": merges.get('count') if merges is not None else 0,
               "merges": merge_list, "row_element_count": len(rows),
               "hidden_row_count": len(hidden_rows)}, f, indent=2)
print("\nSaved metadata to state/utharsika_fresh_meta.json")
