with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if 'viewQueue' in l:
        print(f"viewQueue: line {i+1}")
    if 'queueTableBody' in l:
        print(f"queueTableBody: line {i+1}")
