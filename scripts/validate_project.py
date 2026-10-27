"""Preserve each runner's exit code and record software versus data validation."""
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
commands=[['python3','-m','unittest','discover','-s','tests','-v'],['node','tests/dashboard.test.js'],
 ['python3','-m','observatory.cli','validate','--as-of','2026-10-27T00:00:00-04:00']]
results=[]
for command in commands:
 result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
 results.append({'command':command,'exit_code':result.returncode,'output':result.stdout+result.stderr})
 print(results[-1]['output'])
report={'passed':all(r['exit_code']==0 for r in results),'checks':results,
        'qualification':'Software checks; real-source completeness, research findings and Cube deployment remain unvalidated.'}
(ROOT/'reports/software-validation.json').write_text(json.dumps(report,indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)
