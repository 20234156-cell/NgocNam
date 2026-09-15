import json

with open('logs/audit.jsonl', 'r', encoding='utf-8') as f:
    lines = [json.loads(line) for line in f if 'HS-20268888' in line]

print(f"Total audit records for HS-20268888: {len(lines)}")
import sys
sys.stdout.reconfigure(encoding='utf-8')
for r in lines[-4:]:
    snap = r.get("application_snapshot", {})
    income = snap.get("thu_nhap_thang_vnd", "N/A")
    print(f"Run #{r.get('run_number')} | Req={r.get('request_id')[:8]} | Decision={r.get('decision')} | Trigger={r.get('triggered_by')} | Income={income}")
