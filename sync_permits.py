"""Fetch recently issued permits from Maricopa County's public ArcGIS layer."""
import argparse
import csv
import io
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from server import FIELDS, import_csv

LAYER = ('https://services.arcgis.com/ykpntM6e3tHvzKRJ/arcgis/rest/services/'
         'Building_Permits_(view)/FeatureServer/0')
SOURCE = 'Maricopa County Building Permits'
DATASET = 'https://www.arcgis.com/home/item.html?id=86909eb1ea9149308abaadba377f388f'
PAGE_SIZE = 500
MAX_ROWS = 9000
EXPECTED = {'OBJECTID', 'PermitNumber', 'PermitDescription', 'FullStreetAddress',
            'PermitType', 'WorkClass', 'PermitStatus', 'IssuedDate'}


def fetch_json(url):
    request = Request(url, headers={'User-Agent': 'ArizonaProjectRadar/1.0 (public permit feed)'})
    with urlopen(request, timeout=25) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError('Permit feed response exceeded 2 MB')
    result = json.loads(data)
    if 'error' in result:
        raise ValueError(f"Permit feed error: {result['error'].get('message', result['error'])}")
    return result


def collect(days=14, today=None, fetch=fetch_json):
    if not 1 <= days <= 90:
        raise ValueError('Days must be between 1 and 90')
    metadata = fetch(LAYER + '?f=json')
    fields = {field['name'] for field in metadata.get('fields', [])}
    if not EXPECTED.issubset(fields):
        raise ValueError('County permit feed schema changed; refusing to import')
    since = (today or datetime.now(timezone.utc)).date() - timedelta(days=days)
    where = f"IssuedDate >= DATE '{since.isoformat()}' AND PermitStatus = 'Issued'"
    seen_ids = set()
    output = []
    offset = 0
    while True:
        query = urlencode({'where': where, 'outFields': ','.join(sorted(EXPECTED)),
                           'returnGeometry': 'false', 'orderByFields': 'OBJECTID ASC',
                           'resultOffset': offset, 'resultRecordCount': PAGE_SIZE, 'f': 'json'})
        page = fetch(LAYER + '/query?' + query)
        features = page.get('features')
        if not isinstance(features, list):
            raise ValueError('County permit feed returned no features list')
        for feature in features:
            a = feature['attributes']
            permit_id = str(a.get('PermitNumber') or '').strip()
            if not permit_id or not a.get('IssuedDate') or not a.get('OBJECTID'):
                continue
            if permit_id in seen_ids:
                continue
            seen_ids.add(permit_id)
            issued = datetime.fromtimestamp(a['IssuedDate'] / 1000, timezone.utc).date().isoformat()
            description = str(a.get('PermitDescription') or '').strip()
            work_class = str(a.get('WorkClass') or '').strip()
            output.append({
                'source': SOURCE, 'permit_id': permit_id,
                'description': description or work_class or str(a.get('PermitType') or 'Building permit'),
                'address': str(a.get('FullStreetAddress') or '').strip(),
                'city': '', 'county': 'Maricopa', 'issued_date': issued,
                'permit_type': ' / '.join(filter(None, [str(a.get('PermitType') or '').strip(), work_class])),
                'value': '', 'source_url': DATASET,
            })
        offset += len(features)
        if len(output) > MAX_ROWS:
            raise ValueError('Too many permits in window; retry with fewer days')
        if len(features) < PAGE_SIZE:
            break
        if offset > MAX_ROWS + PAGE_SIZE:
            raise ValueError('Too many feed records; retry with fewer days')
    return output


def sync(days=14, today=None, fetch=fetch_json):
    rows = collect(days, today, fetch)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    result = import_csv(buffer.getvalue())
    return {'fetched': len(rows), **result, 'source': DATASET}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--days', type=int, default=14, help='Issued-date lookback (1–90, default 14)')
    args = parser.parse_args()
    print(json.dumps(sync(args.days), indent=2))
