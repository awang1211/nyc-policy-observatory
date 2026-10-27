from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/observatory.sqlite'
STUDY_START = '2025-10-01'
STUDY_END = '2026-10-01'  # exclusive
BASELINE_START = '2024-10-01'
COUNTIES = {'005': 'BRONX', '047': 'BROOKLYN', '061': 'MANHATTAN',
            '081': 'QUEENS', '085': 'STATEN ISLAND'}
DOMAINS = {
    'housing': ('housing', 'tenant', 'rent', 'building', 'homeless', 'shelter'),
    'transportation': ('street', 'traffic', 'transit', 'bicycle', 'parking', 'pedestrian'),
    'sanitation': ('sanitation', 'waste', 'trash', 'recycling', 'cleaning'),
    'health': ('health', 'hospital', 'mental', 'overdose'),
    'environment': ('climate', 'flood', 'water', 'sewer', 'air quality', 'tree'),
    'education': ('school', 'student', 'child care', 'education'),
    'public_safety': ('police', 'safety', 'fire', 'emergency'),
    'economic_security': ('worker', 'wage', 'employment', 'benefit', 'food'),
    'government_access': ('accessibility', 'language', 'digital', '311', 'government'),
    'parks_culture': ('park', 'recreation', 'library', 'cultural'),
}

def domain_for(title):
    # Discovery tags only; reviewers decide registry domains.
    text = title.casefold()
    hits = [d for d, words in DOMAINS.items() if any(w in text for w in words)]
    return '|'.join(hits) or 'unclassified'
