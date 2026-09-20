"""Import a City of Phoenix PDD issued-permit CSV downloaded from its public search."""
import argparse
import csv
import io
import json
import re
from datetime import datetime
from pathlib import Path

from server import FIELDS, connect, import_csv

SOURCE = 'City of Phoenix PDD Issued Permits'
SOURCE_URL = 'https://apps-secure.phoenix.gov/PDD/Search/IssuedPermit'


def normalized(value):
    return re.sub(r'[^a-z0-9]', '', str(value).lower())


def parse_date(value):
    value = value.strip()
    for fmt in ('%m/%d/%Y %I:%M:%S %p', '%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y'):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f'Invalid issue date: {value!r}')


def parse(content):
    # Phoenix's Create File export has search criteria on line one and headers on line two.
    lines = content.lstrip('\ufeff').splitlines()
    index = next((n for n, line in enumerate(lines[:5])
                  if {'number', 'issuedate', 'address', 'parcel'} <=
                  {normalized(v) for v in next(csv.reader([line]))}), None)
    if index is None:
        raise ValueError('Expected Phoenix PDD issued-permit export headers (Number, Issue Date, Address, Parcel)')
    reader = csv.DictReader(io.StringIO('\n'.join(lines[index:])))
    if not reader.fieldnames:
        raise ValueError('Missing CSV header')
    columns = {normalized(v): v for v in reader.fieldnames}
    for required in ('number', 'issuedate', 'address', 'parcel'):
        if required not in columns:
            raise ValueError(f'Missing Phoenix column: {required}')

    plan_column = 'plannumber' if 'plannumber' in columns else 'plannum'
    if plan_column not in columns:
        raise ValueError('Missing Phoenix column: Plan Num')

    def get(row, key):
        return (row.get(columns.get(key, '')) or '').strip()

    by_permit = {}
    for line_number, row in enumerate(reader, start=index + 2):
        if None in row:
            raise ValueError(f'Extra columns on CSV row {line_number}')
        permit = get(row, 'number')
        if not permit:
            continue
        date = get(row, 'issuedate')
        if not date:
            continue
        kind = ' / '.join(filter(None, (get(row, 'type'), get(row, 'structclass'), get(row, 'use'))))
        address = get(row, 'address')
        record = {'source': SOURCE, 'permit_id': permit,
                     'description': kind or f'Phoenix issued permit {permit}',
                     'address': address, 'city': 'Phoenix', 'county': 'Maricopa',
                     'issued_date': parse_date(date), 'permit_type': kind,
                     'value': get(row, 'valuation'), 'source_url': SOURCE_URL}
        contractor = get(row, 'contractor')
        # The export labels a contractor but does not establish its GC role.
        details = (get(row, plan_column), get(row, 'parcel'), get(row, 'owner'), contractor)
        if permit in by_permit:
            original, prior = by_permit[permit]
            combined = tuple(old or new for old, new in zip(prior, details))
            if combined[3].upper() in ('OWNER', 'TO BE BID', 'UNKNOWN', 'N/A') and contractor and contractor.upper() not in ('OWNER', 'TO BE BID', 'UNKNOWN', 'N/A'):
                combined = (*combined[:3], contractor)
            by_permit[permit] = (original, combined)
        else:
            by_permit[permit] = (record, details)
        if len(by_permit) > 9000:
            raise ValueError('Import exceeds 9,000 issued permits; narrow the date range')
    if not by_permit:
        raise ValueError('No issued permits found in the Phoenix export')
    rows = [record for record, _ in by_permit.values()]
    extra = [details for _, details in by_permit.values()]
    return rows, extra


def import_file(content):
    rows, extra = parse(content)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    result = import_csv(buffer.getvalue())
    # Fill investigation fields only when blank. Keep the raw reported contractor
    # separate: a listed trade contractor must not be asserted to be the GC.
    with connect() as db:
        for row, (plan, parcel, owner, contractor) in zip(rows, extra):
            db.execute('''UPDATE permits SET
                plan_number=CASE WHEN plan_number='' THEN ? ELSE plan_number END,
                parcel=CASE WHEN parcel='' THEN ? ELSE parcel END,
                owner=CASE WHEN owner='' THEN ? ELSE owner END,
                source_contractor=?
                WHERE source=? AND permit_id=?''',
                (plan, parcel, owner, contractor, SOURCE, row['permit_id']))
    return {'processed': len(rows), **result, 'source': SOURCE_URL}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', type=Path, help='CSV from Phoenix PDD Issued Permit Data Search → Create File')
    args = parser.parse_args()
    if args.csv_file.stat().st_size > 5_000_000:
        parser.error('CSV exceeds 5 MB; export a smaller date range')
    print(json.dumps(import_file(args.csv_file.read_text(encoding='utf-8-sig')), indent=2))
