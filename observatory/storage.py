import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from .config import ROOT, DB

def now():
    return datetime.now(timezone.utc).isoformat()

def connect(path=DB):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.executescript((ROOT / 'sql/schema.sql').read_text())
    return db

def archive(db, url, body, content_type='application/json'):
    sha = hashlib.sha256(body).hexdigest()
    identity = hashlib.sha256((url + sha).encode()).hexdigest()
    path = ROOT / 'data/raw' / f'{identity}.bin'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    db.execute('INSERT OR IGNORE INTO source_artifact VALUES (?,?,?,?,?,?)',
               (identity, url, now(), sha, str(path.relative_to(ROOT)), content_type))
    db.commit()
    return identity

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
