import json
from pathlib import Path

BASE_URL = 'https://github.com/cpatagon/retc-rm/blob/master/'
report_path = Path('docs/informes/informe_brechas.md')
section_title = '## Gráficos 2023 por comuna y contaminante'

paths = sorted(Path('outputs/graficos/emisiones_acumuladas_2023').glob('*.png'))
if not paths:
    raise SystemExit('No se encontraron PNG en outputs/graficos/emisiones_acumuladas_2023/')

section_lines = [section_title]
for path in paths:
    contaminant = path.stem.replace('_comunas_2023', '')
    url = BASE_URL + path.as_posix()
    section_lines.append(f'- [{contaminant}]({url})')
section_text = '\n'.join(section_lines) + '\n'

text = report_path.read_text(encoding='utf-8')
if section_title in text:
    # reemplazar sección existente
    parts = text.split(section_title)
    prefix = parts[0]
    suffix_parts = parts[1].split('\n## ', 1)
    suffix = ('\n## ' + suffix_parts[1]) if len(suffix_parts) > 1 else ''
    new_text = prefix + section_text + suffix
else:
    new_text = text.rstrip() + '\n\n' + section_text

report_path.write_text(new_text, encoding='utf-8')
print('Sección de gráficos agregada/actualizada en', report_path)
