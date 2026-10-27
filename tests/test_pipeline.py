"""Synthetic fixtures are isolated in temporary databases, never research exports."""
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from observatory.storage import connect, archive
from observatory.metrics import summarize, build_metrics, aggregate, quantile
from observatory.validate import validate
from observatory.ingest import ingest_311, ingest_acs, import_policies, import_agency, import_links

AS_OF = '2026-10-27T00:00:00-04:00'

def row(created, closed=None, key='1', **extra):
    return {'request_id': key,'created_at': created,'closed_at':closed,'agency':'TEST',
            'service':'Synthetic fixture','borough':'QUEENS','community_district':'01 QUEENS',
            'incident_zip':None,'status':'Closed' if closed else 'Open',**extra}

class MetricsTests(unittest.TestCase):
    def test_known_values_and_invalid_closure(self):
        values = summarize([row('2026-01-01','2026-01-02'),row('2026-01-01','2026-02-02'),
                            row('2026-01-01'),row('2026-01-01','2025-12-31')],AS_OF)
        self.assertEqual(values['requests'],4)
        self.assertEqual(values['eligible_30d'],3)
        self.assertEqual(values['closed_30d'],1)
        self.assertEqual(values['invalid_closure'],1)
        self.assertEqual(values['unresolved_asof'],2)
        self.assertEqual(values['median_closed_hours'],396)
        self.assertEqual(values['p90_closed_hours'],693.6)

    def test_matched_recent_cohorts(self):
        values = summarize([row('2026-09-28','2026-09-29'),row('2025-09-28','2025-09-29'),
                            row('2026-09-26','2026-09-27'),row('2025-09-26','2025-09-27')],AS_OF)
        self.assertEqual(values['requests'],4)
        self.assertEqual(values['eligible_30d'],2)
        self.assertEqual(values['closed_30d'],2)

    def test_dst_elapsed_hours(self):
        values = summarize([row('2026-03-08T00:00:00','2026-03-09T00:00:00')],AS_OF)
        self.assertEqual(values['closed_hours_sum'],23)

    def test_exact_30day_boundary(self):
        values = summarize([row('2026-01-01','2026-01-31'),row('2026-01-01','2026-01-31T00:00:01')],AS_OF)
        self.assertEqual(values['closed_30d'],1)

    def test_future_closures_are_unresolved_asof(self):
        values = summarize([row('2026-01-01','2026-11-01')],AS_OF)
        self.assertEqual(values['unresolved_asof'],1)
        self.assertEqual(values['closed_observed'],0)
        self.assertIsNone(values['median_closed_hours'])

    def test_weighted_rates_not_mean_of_rates(self):
        a = summarize([row('2026-01-01','2026-01-02')],AS_OF)
        b = summarize([row('2026-01-01')]*9,AS_OF)
        self.assertEqual(aggregate([a,b])['closure_30d_rate'],.1)
        self.assertIsNone(aggregate([])['closure_30d_rate'])

class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=connect(Path(self.tmp.name)/'test.sqlite')
        self.artifact=archive(self.db,'https://www.nyc.gov/synthetic-fixture',b'unit test fixture only')

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def insert(self, item):
        self.db.execute('INSERT INTO service_request VALUES (?,?,?,?,?,?,?,?,?,?)',
            tuple(item[k] for k in ('request_id','created_at','closed_at','agency','service','borough',
                  'community_district','incident_zip','status'))+(self.artifact,))

    def test_independent_reconciliation_and_tamper_detection(self):
        for i,r in enumerate([row('2025-01-01','2025-01-05'),row('2026-01-01'),
                               row('2026-09-28','2026-09-29'),row('2026-02-01','2026-01-01')]):
            r['request_id']=str(i);self.insert(r)
        build_metrics(self.db,AS_OF)
        result=validate(self.db,AS_OF)
        self.assertTrue(result['passed'],result)
        self.db.execute('UPDATE service_metrics SET requests=requests+1')
        self.assertFalse(validate(self.db,AS_OF)['passed'])

    def test_keyset_pagination_upsert_and_partial_status(self):
        fields=['unique_key','created_date','closed_date','agency','complaint_type','borough','community_board','incident_zip','status']
        metadata={'columns':[{'fieldName':f} for f in fields]}
        responses=[metadata,[{'unique_key':'1','created_date':'2024-10-01T01:00:00','agency':'TEST','complaint_type':'Fixture'}]]
        def retrieve(db,url,headers=None):return responses.pop(0),self.artifact
        with patch('observatory.ingest.fetch_json',side_effect=retrieve):
            result=ingest_311(self.db,max_pages=1,page_size=1)
        self.assertEqual(result['status'],'partial')
        responses.extend([metadata,[{'unique_key':'1','created_date':'2024-10-01T01:00:00','closed_date':'2024-10-02','agency':'TEST','complaint_type':'Fixture'}]])
        with patch('observatory.ingest.fetch_json',side_effect=retrieve):ingest_311(self.db,max_pages=1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM service_request').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT closed_at FROM service_request').fetchone()[0],'2024-10-02')

    def test_acs_county_grain(self):
        header=['NAME','B01003_001E','B17001_001E','B17001_002E','B19013_001E','state','county']
        rows=[header]+[['Fixture','100','90','9','50000','36',fips] for fips in ['005','047','061','081','085']]
        with patch('observatory.ingest.fetch_json',return_value=(rows,self.artifact)):
            self.assertEqual(ingest_acs(self.db)['rows'],5)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM socioeconomic').fetchone()[0],5)

    def csv_path(self,rows):
        path=Path(self.tmp.name)/'input.csv'
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        return path

    def test_policy_dedup_and_evidence_hierarchy(self):
        base={'policy_id':'fixture:1','title':'Synthetic test policy','domain':'housing','agency':'TEST',
              'evidence_type':'implementation_verified','event_date':'2026-02-01','source_url':'https://www.nyc.gov/fixture',
              'evidence_quote':'Synthetic fixture quotation only.','reviewer':'unit-test'}
        with patch('observatory.ingest.verify_quote',return_value=self.artifact):
            import_policies(self.db,self.csv_path([base,base]))
            base|={'evidence_type':'announced','event_date':'2025-11-01'}
            import_policies(self.db,self.csv_path([base]))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM policy').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM policy_evidence').fetchone()[0],2)
        p=self.db.execute('SELECT * FROM policy').fetchone()
        self.assertEqual(p['verified_status'],'implementation_verified')
        self.assertEqual(p['announcement_date'],'2025-11-01')

    def test_agency_period_and_link_import(self):
        r={'indicator_id':'fixture','agency':'TEST','indicator':'Fixture','period_start':'2025-07-01',
           'period_end':'2026-07-01','value':'90','unit':'percent','direction':'higher_is_better',
           'source_url':'https://www.nyc.gov/fixture','evidence_quote':'Synthetic fixture quotation only.'}
        with patch('observatory.ingest.verify_quote',return_value=self.artifact):
            self.assertEqual(import_agency(self.db,self.csv_path([r])),1)
        self.assertEqual(self.db.execute('SELECT value FROM agency_performance').fetchone()[0],90)

    def test_missing_source_quote_is_rejected(self):
        from observatory.ingest import verify_quote
        with patch('observatory.ingest.fetch',return_value=(b'<html>Another text.</html>','text/html')):
            with self.assertRaises(ValueError):verify_quote(self.db,'https://www.nyc.gov/test','Quotation not present in source text.')
        with self.assertRaises(ValueError):verify_quote(self.db,'https://example.com','Some untrusted quotation from another source.')

if __name__=='__main__':unittest.main()
