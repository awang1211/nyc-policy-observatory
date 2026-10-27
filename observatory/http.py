"""Verified TLS, bounded retries, and no credential-bearing logs."""
import json
import time
import urllib.error
import urllib.request

class SourceError(RuntimeError):
    pass

def fetch(url, headers=None, attempts=4):
    request = urllib.request.Request(url, headers={
        'User-Agent': 'NYCPolicyObservatory/0.1 (public-interest research)',
        'Accept': 'application/json,text/html,application/xml', **(headers or {})})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read(), response.headers.get('Content-Type', '')
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise SourceError(f'HTTP {error.code}; source retrieval failed') from None
            retry = error.headers.get('Retry-After', '')
            time.sleep(min(float(retry) if retry.isdigit() else 2 ** attempt, 30))
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == attempts - 1:
                raise SourceError('Network/proxy connection failed; inspect environment access policy') from None
            time.sleep(2 ** attempt)
    raise SourceError('Retrieval failed')

def fetch_json(db, url, headers=None):
    from .storage import archive
    body, mime = fetch(url, headers)
    try:
        value = json.loads(body)
    except ValueError:
        raise SourceError('Expected JSON; source returned another representation') from None
    return value, archive(db, url, body, mime)
