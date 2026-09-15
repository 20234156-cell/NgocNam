import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('app/cockpit.html', 'r', encoding='utf-8') as f:
    text = f.read()

checks = {
    "batchAssessModal in DOM": 'id="batchAssessModal"' in text,
    "queueBatchBar in DOM": 'id="queueBatchBar"' in text,
    "selectAllQueueCheckbox in DOM": 'id="selectAllQueueCheckbox"' in text,
    "exportSelectedQueueToExcel defined": 'function exportSelectedQueueToExcel' in text,
    "exportAllQueueToExcel defined": 'function exportAllQueueToExcel' in text,
    "exportSingleQueueToExcel defined": 'function exportSingleQueueToExcel' in text,
    "openBatchAssessModal defined": 'function openBatchAssessModal' in text,
    "closeBatchAssessModal defined": 'function closeBatchAssessModal' in text,
    "exportBatchModalToExcel defined": 'function exportBatchModalToExcel' in text,
    "simulate-stress API call": 'simulate-stress' in text,
    "committee-decision API call": 'audit/committee-decision' in text,
    "auditDetailModal in DOM": 'id="auditDetailModal"' in text,
    "decisionModal in DOM": 'id="decisionModal"' in text
}

for k, v in checks.items():
    print(f"{k:40}: {v}")
