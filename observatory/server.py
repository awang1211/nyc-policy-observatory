import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from .config import ROOT
from .http import SourceError

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'web'), **kwargs)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/api/dashboard':
            try:
                snapshot = json.loads((ROOT/'data/processed/dashboard.json').read_text())
                if parse_qs(url.query).get('source') == ['cube']:
                    from .cube import service_metrics
                    rows = service_metrics()
                    keys = ('period','month','agency','service','borough','community_district')
                    counts = ('requests','eligible_30d','closed_30d','unresolved_asof','invalid_closure','closed_observed')
                    def signature(records):
                        return {tuple(r[k] for k in keys):tuple(r[k] for k in counts) for r in records}
                    if signature(rows) != signature(snapshot['metrics']):
                        raise SourceError('Cube deployment does not reconcile to this export')
                    snapshot['metrics'] = rows
                    snapshot['metric_backend'] = 'Cube REST; registry and provenance from local export'
                else:
                    snapshot['metric_backend'] = 'Local verified-export contract'
                self.respond(snapshot)
            except (OSError, ValueError, SourceError):
                self.respond({'error': 'Snapshot or Cube source unavailable. Run export; inspect server configuration.'}, 503)
            return
        if url.path == '/api/health':
            self.respond({'status':'ok', 'snapshot_available': (ROOT/'data/processed/dashboard.json').is_file()})
            return
        super().do_GET()

    def respond(self, body, status=200):
        data = json.dumps(body, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers()
        self.wfile.write(data)

def serve(port=8000):
    server = ThreadingHTTPServer(('127.0.0.1',port), Handler)
    print(f'Observatory server listening on port {port}', flush=True)
    server.serve_forever()
