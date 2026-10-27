"""Non-destructive access probes; no credential values in outputs."""
import concurrent.futures
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
SOURCES={
 'cube_workspace':'https://anruow.cubecloud.dev/d/1',
 '311_metadata':'https://data.cityofnewyork.us/api/views/erm2-nwe9.json',
 'nyc_official':'https://www.nyc.gov',
 'census_acs':'https://api.census.gov/data/2024/acs/acs5?get=NAME&for=county:061&in=state:36',
 'council_legistar':'https://webapi.legistar.com/v1/nyc/Matters?$top=1'
}
def probe(item):
 name,url=item
 try:
  with urllib.request.urlopen(url,timeout=30) as r:
   r.read(100);return name,{'url':url,'status':r.status,'content_type':r.headers.get('Content-Type')}
 except urllib.error.HTTPError as e:return name,{'url':url,'status':e.code,'outcome':'http_error'}
 except urllib.error.URLError as e:
  return name,{'url':url,'outcome':'proxy_policy_denied' if '403' in str(e.reason) else 'network_error'}
 except OSError:return name,{'url':url,'outcome':'network_error'}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as p:results=dict(p.map(probe,SOURCES.items()))
report={'checked_at':datetime.now(timezone.utc).isoformat(),'sources':results,
        'bindings_present':{k:bool(os.getenv(k)) for k in ('CUBE_API_URL','CUBE_API_TOKEN','DATABASE_URL','SOCRATA_APP_TOKEN')},
        'starter_kit':'No attachment or local starter-kit file available in this session'}
path=Path(__file__).resolve().parents[1]/'reports/access.json';path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
