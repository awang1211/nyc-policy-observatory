import argparse
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from .storage import connect, write_json
from .config import ROOT
from .http import SourceError

def main():
    parser = argparse.ArgumentParser(description='NYC Policy Implementation Observatory')
    parser.add_argument('command', choices=['init','ingest-311','ingest-acs','discover-policies','discover-events',
        'discover-news','discover-open-data','inspect-open-data','ingest-open-data','verify-open-data',
        'import-policies','import-agency','import-links','export','validate','inspect-cube',
        'load-postgres','load-postgres-sources','serve'])
    parser.add_argument('--input')
    parser.add_argument('--as-of', default=datetime.now(ZoneInfo('America/New_York')).isoformat())
    parser.add_argument('--max-pages',type=int)
    parser.add_argument('--port',type=int,default=8000)
    args = parser.parse_args()
    try:
        db = connect()
        if args.command == 'init':
            result = {'database':'initialized'}
        elif args.command == 'ingest-311':
            from .ingest import ingest_311
            result = ingest_311(db, args.max_pages)
        elif args.command == 'ingest-acs':
            from .ingest import ingest_acs
            result = ingest_acs(db)
        elif args.command == 'discover-policies':
            from .ingest import ingest_legislation
            result = ingest_legislation(db, args.max_pages)
        elif args.command == 'discover-events':
            from .ingest import ingest_council_events
            result = ingest_council_events(db,args.max_pages)
        elif args.command == 'discover-news':
            from .ingest import discover_official_news
            result = discover_official_news(db,args.input or ROOT/'data/inputs/news_seeds.csv',args.max_pages or 200)
        elif args.command == 'discover-open-data':
            from .ingest import discover_open_data_catalog
            result = discover_open_data_catalog(db)
        elif args.command == 'inspect-open-data':
            from .ingest import inspect_open_data_sources
            result = inspect_open_data_sources(db)
        elif args.command == 'ingest-open-data':
            from .ingest import ingest_selected_open_data
            result = ingest_selected_open_data(db)
        elif args.command == 'verify-open-data':
            council = db.execute("SELECT COUNT(*) FROM policy_candidate WHERE source_id LIKE 'nyc-open-data-council:%'").fetchone()[0]
            performance = db.execute('SELECT COUNT(*) FROM agency_performance').fetchone()[0]
            print(f'::notice title=Imported official data::Council records: {council}; agency performance records: {performance}')
            if council == 0 or performance == 0:
                raise SourceError('Selected official datasets produced zero Council or agency performance records')
            result = {'council_records': council, 'agency_performance_records': performance}
        elif args.command.startswith('import-'):
            if not args.input:
                parser.error('--input CSV is required')
            from .ingest import import_policies, import_agency, import_links
            result = {'imported': {'import-policies':import_policies,'import-agency':import_agency,
                                   'import-links':import_links}[args.command](db,args.input)}
        elif args.command == 'export':
            from .export import export
            result = export(db,args.as_of)
            result = {k: result[k] for k in ('source_status','counts','readiness','as_of')}
        elif args.command == 'validate':
            from .validate import validate
            result = validate(db,args.as_of)
            write_json(ROOT/'reports/validation.json',result)
            print(json.dumps(result,indent=2))
            return 0 if result['passed'] else 1
        elif args.command == 'inspect-cube':
            from .cube import inspect_cube
            result = inspect_cube()
        elif args.command == 'load-postgres':
            from .cube import load_postgres
            result = load_postgres(db)
        elif args.command == 'load-postgres-sources':
            from .cube import load_postgres_sources
            result = load_postgres_sources(db)
        elif args.command == 'serve':
            from .server import serve
            serve(args.port)
            return 0
        print(json.dumps(result,indent=2))
        return 0
    except (SourceError, ValueError) as error:
        print(f'Blocked: {error}',file=sys.stderr)
        return 2

if __name__ == '__main__':
    sys.exit(main())
