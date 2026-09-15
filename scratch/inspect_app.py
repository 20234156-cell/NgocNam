import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Find main sections
sections = re.findall(r'id=["\']([a-zA-Z0-9_\-]+)["\']', text)
views = [s for s in sections if 'view' in s.lower() or 'section' in s.lower() or 'tab' in s.lower() or 'modal' in s.lower() or 'panel' in s.lower()]
print('Views / Sections / Modals:', views)

# Find all JS functions
funcs = re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', text)
print(f'Functions ({len(funcs)}):', funcs)
