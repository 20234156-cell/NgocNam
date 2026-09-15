import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    text = f.read()

def print_func(name):
    idx = text.find(f"function {name}")
    if idx != -1:
        print(f"=== FUNCTION {name} ===")
        print(text[idx:idx+1500])
        print("...\n")
    else:
        print(f"Function {name} not found!")

print_func("runStressSimulation")
print_func("issueOfficialDecision")
print_func("setupCommitteeEvents")
print_func("loadQueueFromApi")
