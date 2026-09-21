import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const snapshot = JSON.parse(
  readFileSync(new URL('../data/dashboard-snapshot.json', import.meta.url), 'utf8'),
);

const expectedBoroughs = ['BRONX', 'BROOKLYN', 'MANHATTAN', 'QUEENS', 'STATEN ISLAND'];
const expectedDomains = ['complaints', 'permit_records', 'violations'];
const allowedTiers = new Set(['LOW', 'MODERATE', 'HIGH', 'CRITICAL']);
const allowedQualityStatuses = new Set(['PASS', 'WARN', 'ERROR']);

assert.match(snapshot.metadata.snapshotDate, /^\d{4}-\d{2}-\d{2}$/);
assert.equal(snapshot.boroughs.length, 5);
assert.deepEqual(snapshot.boroughs.map((row) => row.borough).sort(), expectedBoroughs);
assert.deepEqual(snapshot.quality.map((row) => row.domain).sort(), expectedDomains);

for (const row of snapshot.quality) {
  assert.ok(row.totalRecordCount > 0, `${row.domain} must contain source records`);
  assert.ok(row.buildingKeyCoveragePct >= 0 && row.buildingKeyCoveragePct <= 100);
  assert.ok(allowedQualityStatuses.has(row.qualityStatus));
}

const boroughTotals = snapshot.boroughs.reduce(
  (total, row) => ({
    buildings: total.buildings + row.observedBuildingCount,
    priority: total.priority + row.priorityBuildingCount,
    complaints: total.complaints + row.openComplaintCount,
    violations: total.violations + row.openViolationCount,
    openItems: total.openItems + row.totalOpenComplianceItemCount,
  }),
  { buildings: 0, priority: 0, complaints: 0, violations: 0, openItems: 0 },
);

assert.equal(boroughTotals.buildings, snapshot.overview.observedBuildingCount);
assert.equal(boroughTotals.priority, snapshot.overview.priorityBuildingCount);
assert.equal(boroughTotals.complaints, snapshot.overview.openComplaintCount);
assert.equal(boroughTotals.violations, snapshot.overview.openViolationCount);
assert.equal(boroughTotals.openItems, snapshot.overview.totalOpenComplianceItemCount);

const tierTotal = snapshot.attentionTiers.reduce((total, row) => {
  assert.ok(allowedTiers.has(row.tier));
  return total + row.buildingCount;
}, 0);
assert.equal(tierTotal, snapshot.overview.observedBuildingCount);

const bins = new Set();
for (const building of snapshot.priorityBuildings) {
  assert.match(building.bin, /^[1-5][0-9]{6}$/);
  assert.doesNotMatch(building.bin, /^[1-5]0{6}$/);
  assert.ok(!bins.has(building.bin), `Duplicate BIN in priority queue: ${building.bin}`);
  bins.add(building.bin);
  assert.ok(allowedTiers.has(building.attentionTier));
  assert.equal(
    building.totalOpenComplianceItemCount,
    building.openComplaintCount + building.openViolationCount,
  );
}

console.log('Dashboard snapshot contract passed.');
console.log(`  snapshot date: ${snapshot.metadata.snapshotDate}`);
console.log(`  observed buildings: ${snapshot.overview.observedBuildingCount}`);
console.log(`  priority building rows: ${snapshot.priorityBuildings.length}`);
