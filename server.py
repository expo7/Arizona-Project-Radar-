"""Local-first permit lead review server. Python 3.11+, no dependencies."""
import csv
import io
import json
import os
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('RADAR_DB', ROOT / 'radar.sqlite3'))
FIELDS = ('source', 'permit_id', 'description', 'address', 'city', 'county', 'issued_date', 'permit_type', 'value', 'source_url')


def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS permits (
        id INTEGER PRIMARY KEY, source TEXT NOT NULL, permit_id TEXT NOT NULL,
        description TEXT NOT NULL, address TEXT NOT NULL, city TEXT NOT NULL,
        county TEXT NOT NULL, issued_date TEXT NOT NULL, permit_type TEXT NOT NULL,
        value TEXT NOT NULL, source_url TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new',
        notes TEXT NOT NULL DEFAULT '', imported_at TEXT NOT NULL,
        UNIQUE(source, permit_id))''')
    return db


def import_csv(content):
    reader = csv.DictReader(io.StringIO(content.lstrip('\ufeff')))
    if not reader.fieldnames or not set(FIELDS).issubset(reader.fieldnames):
        raise ValueError('CSV must include: ' + ', '.join(FIELDS))
    rows = list(reader)
    if len(rows) > 10000:
        raise ValueError('Import limit is 10,000 rows')
    prepared = []
    for n, row in enumerate(rows, start=2):
        item = {k: (row.get(k) or '').strip() for k in FIELDS}
        if not item['source'] or not item['permit_id'] or not item['description']:
            raise ValueError(f'Row {n} needs source, permit_id and description')
        if item['issued_date']:
            try:
                datetime.strptime(item['issued_date'], '%Y-%m-%d')
            except ValueError:
                raise ValueError(f'Row {n}: issued_date must be YYYY-MM-DD') from None
        url = item['source_url']
        if url and urlparse(url).scheme not in ('http', 'https'):
            raise ValueError(f'Row {n}: source_url must start with http:// or https://')
        prepared.append(tuple(item[k] for k in FIELDS) + (datetime.now().isoformat(timespec='seconds'),))
    with connect() as db:
        before = db.total_changes
        db.executemany('''INSERT OR IGNORE INTO permits
            (source, permit_id, description, address, city, county, issued_date,
             permit_type, value, source_url, imported_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''', prepared)
        return {'added': db.total_changes - before, 'skipped': len(rows) - (db.total_changes - before)}


class Handler(BaseHTTPRequestHandler):
    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        size = int(self.headers.get('Content-Length', '0'))
        if size > 5_000_000 or size < 1:
            raise ValueError('Request must be between 1 byte and 5 MB')
        return json.loads(self.rfile.read(size))

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/api/health':
            with connect() as db:
                count = db.execute('SELECT count(*) FROM permits').fetchone()[0]
            return self.send_json(200, {'ok': True, 'records': count})
        if path == '/api/permits':
            with connect() as db:
                rows = [dict(r) for r in db.execute('SELECT * FROM permits ORDER BY issued_date DESC, id DESC LIMIT 10000')]
            return self.send_json(200, {'permits': rows})
        filename = 'index.html' if path == '/' else path.removeprefix('/')
        if filename not in ('index.html', 'app.js', 'style.css'):
            return self.send_error(404)
        file = ROOT / 'static' / filename
        content = file.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', {'index.html': 'text/html', 'app.js': 'text/javascript', 'style.css': 'text/css'}[filename] + '; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        try:
            data = self.body()
            if self.path == '/api/import':
                if not isinstance(data.get('csv'), str):
                    raise ValueError('Expected CSV text')
                return self.send_json(200, import_csv(data['csv']))
            if self.path.startswith('/api/permits/'):
                record_id = int(self.path.rsplit('/', 1)[-1])
                status = data.get('status')
                notes = data.get('notes')
                if status not in ('new', 'reviewing', 'qualified', 'dismissed') or not isinstance(notes, str) or len(notes) > 2000:
                    raise ValueError('Invalid status or notes')
                with connect() as db:
                    result = db.execute('UPDATE permits SET status=?, notes=? WHERE id=?', (status, notes, record_id))
                return self.send_json(200 if result.rowcount else 404, {'saved': bool(result.rowcount)})
            return self.send_error(404)
        except (ValueError, KeyError, json.JSONDecodeError) as error:
            self.send_json(400, {'error': str(error)})


if __name__ == '__main__':
    host = os.environ.get('RADAR_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))
    print(f'Arizona Project Radar: http://{host}:{port}', flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()
