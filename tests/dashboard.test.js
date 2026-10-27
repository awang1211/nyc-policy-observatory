import test from 'node:test';
import assert from 'node:assert/strict';
import {aggregate,filterMetrics,groupCompare,escapeHTML} from '../web/metrics.js';
const rows=[
 {period:'study',month:'2026-01',borough:'QUEENS',agency:'A',service:'S',community_district:'01 QUEENS',requests:10,eligible_30d:10,closed_30d:1},
 {period:'baseline',month:'2025-01',borough:'QUEENS',agency:'A',service:'S',community_district:'01 QUEENS',requests:5,eligible_30d:5,closed_30d:5},
 {period:'study',month:'2026-02',borough:'BRONX',agency:'B',service:'S',community_district:'01 BRONX',requests:1,eligible_30d:1,closed_30d:1}
];
test('period filtering preserves seasonal comparator',()=>assert.deepEqual(filterMetrics(rows,{month:'2026-01'}),rows.slice(0,2)));
test('filters intersect and all removes restrictions',()=>{assert.equal(filterMetrics(rows,{borough:'QUEENS',agency:'B'}).length,0);assert.equal(filterMetrics(rows,{}).length,3);});
test('weighted closure uses ratio of sums',()=>assert.equal(aggregate([rows[0],rows[2]]).closure_30d_rate,2/11));
test('comparison keeps missing baseline unavailable',()=>{let g=groupCompare(rows,r=>r.borough);assert.equal(g.find(r=>r.label==='BRONX').baseline.closure_30d_rate,null);});
test('untrusted source text is escaped',()=>assert.equal(escapeHTML('<script>"&'), '&lt;script&gt;&quot;&amp;'));
