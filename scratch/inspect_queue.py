import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find("function renderQueuePage")
if idx != -1:
    print(text[idx:idx+2000])
