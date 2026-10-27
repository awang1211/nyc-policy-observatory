"""Request-grain metrics; no averages of averages or subgroup percentiles."""
import hashlib
from itertools import groupby
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .config import BASELINE_START, STUDY_START, STUDY_END

NY = ZoneInfo('America/New_York')

def timestamp(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    # NYC 311 floating timestamps are interpreted in America/New_York.
    return (dt.replace(tzinfo=NY) if dt.tzinfo is None else dt).astimezone(ZoneInfo('UTC'))

def quantile(values, p):
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * p
    lo, hi = int(index), min(int(index) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (index - lo)

def period_for(created):
    day = created[:10]
    if BASELINE_START <= day < STUDY_START:
        return 'baseline'
    if STUDY_START <= day < STUDY_END:
        return 'study'
    return None

def matched_maturity(created, as_of):
    # Both periods use the study-period counterpart's 30-day maturity.
    # No Feb 29 occurs in either selected period.
    local = created.astimezone(NY)
    comparison = local.replace(year=local.year + 1) if local.date().isoformat() < STUDY_START else local
    return comparison.astimezone(ZoneInfo('UTC')) + timedelta(days=30) <= as_of

def summarize(rows, as_of):
    cutoff = timestamp(as_of)
    total = eligible = closed30 = unresolved = invalid = closed_count = 0
    durations = []
    for row in rows:
        created = timestamp(row['created_at'])
        if created > cutoff:
            continue
        total += 1
        closed = timestamp(row['closed_at']) if row['closed_at'] else None
        bad = closed is not None and closed < created
        invalid += int(bad)
        observed = closed is not None and not bad and closed <= cutoff
        unresolved += int(not observed)
        # Invalid timestamps remain visible, but do not enter the closure rate denominator.
        mature = matched_maturity(created, cutoff) and not bad
        eligible += int(mature)
        if observed:
            hours = (closed - created).total_seconds() / 3600
            durations.append(hours)
            closed_count += 1
            closed30 += int(mature and hours <= 30 * 24)
    return {'requests': total, 'eligible_30d': eligible, 'closed_30d': closed30,
            'unresolved_asof': unresolved, 'invalid_closure': invalid,
            'closed_observed': closed_count, 'closed_hours_sum': sum(durations),
            'median_closed_hours': quantile(durations, .5), 'p90_closed_hours': quantile(durations, .9)}

def build_metrics(db, as_of):
    db.execute('DELETE FROM service_metrics')
    cursor = db.execute('SELECT * FROM service_request WHERE created_at>=? AND created_at<? '
                        'ORDER BY substr(created_at,1,7),agency,service,borough,community_district',
                        (BASELINE_START, STUDY_END))
    def group_key(row):
        return (period_for(row['created_at']), row['created_at'][:7], row['agency'],
                row['service'], row['borough'], row['community_district'])
    count = 0
    for key, rows in groupby(cursor, group_key):
        values = summarize(rows, as_of)
        metric_id = hashlib.sha256('|'.join(key).encode()).hexdigest()
        db.execute('INSERT INTO service_metrics VALUES (' + ','.join('?' for _ in range(16)) + ')',
                   (metric_id,) + key + tuple(values.values()))
        count += 1
    db.commit()
    return count

def ratio(numerator, denominator):
    return numerator / denominator if denominator else None

def aggregate(rows):
    keys = ('requests','eligible_30d','closed_30d','unresolved_asof','invalid_closure',
            'closed_observed','closed_hours_sum')
    out = {k: sum(row[k] for row in rows) for k in keys}
    out['closure_30d_rate'] = ratio(out['closed_30d'], out['eligible_30d'])
    out['mean_closed_hours'] = ratio(out['closed_hours_sum'], out['closed_observed'])
    return out
