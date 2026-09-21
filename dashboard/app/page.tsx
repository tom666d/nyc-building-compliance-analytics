'use client';

import { useMemo, useState } from 'react';
import snapshot from '../data/dashboard-snapshot.json';

type View = 'overview' | 'buildings' | 'quality';

const viewCopy: Record<View, { eyebrow: string; title: string; description: string }> = {
  overview: {
    eyebrow: 'Operations command center',
    title: 'Building compliance overview',
    description: 'Prioritize unresolved workload and compare the observed source slice across boroughs.',
  },
  buildings: {
    eyebrow: 'Building-level investigation',
    title: 'Priority building explorer',
    description: 'Move from portfolio metrics to the buildings that need review first.',
  },
  quality: {
    eyebrow: 'Trust and release readiness',
    title: 'Data quality monitor',
    description: 'Make source coverage, build evidence, and known limitations visible to every user.',
  },
};

const integer = new Intl.NumberFormat('en-US');

function formatInteger(value: number) {
  return integer.format(value);
}

function titleCase(value: string) {
  return value.toLowerCase().replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());
}

function Overview({ boroughFilter }: { boroughFilter: string }) {
  const selected = snapshot.boroughs.find((row) => row.borough === boroughFilter);
  const metrics = selected ?? snapshot.overview;
  const filteredBuildings = selected
    ? snapshot.priorityBuildings.filter((row) => row.borough === selected.borough)
    : snapshot.priorityBuildings;
  const maxWorkload = Math.max(...snapshot.boroughs.map((row) => row.totalOpenComplianceItemCount));

  return (
    <>
      <section className="kpi-grid" aria-label="Key performance indicators">
        <article className="kpi-card">
          <span>Priority buildings</span>
          <strong>{formatInteger(metrics.priorityBuildingCount)}</strong>
          <small>HIGH or CRITICAL attention tier</small>
        </article>
        <article className="kpi-card">
          <span>Open complaints</span>
          <strong>{formatInteger(metrics.openComplaintCount)}</strong>
          <small>Records mapped to ACTIVE</small>
        </article>
        <article className="kpi-card">
          <span>Open violations</span>
          <strong>{formatInteger(metrics.openViolationCount)}</strong>
          <small>Legacy records mapped to ACTIVE</small>
        </article>
        <article className="kpi-card">
          <span>Median resolution time</span>
          <strong>{snapshot.overview.medianComplaintResolutionDays12m} <em>days</em></strong>
          <small>Citywide observed sample · {snapshot.overview.resolvedComplaintCount12m} resolved records</small>
        </article>
      </section>

      <section className="overview-grid">
        <article className="panel workload-panel">
          <div className="panel-heading">
            <div><p>Current workload</p><h2>Open items by borough</h2></div>
            <div className="legend" aria-label="Chart legend"><span className="complaint-dot" />Complaints<span className="violation-dot" />Violations</div>
          </div>
          <div className="workload-chart" role="img" aria-label="Open complaints and violations by borough">
            {snapshot.boroughs.map((row) => {
              const complaintWidth = maxWorkload ? (row.openComplaintCount / maxWorkload) * 100 : 0;
              const violationWidth = maxWorkload ? (row.openViolationCount / maxWorkload) * 100 : 0;
              return (
                <div className="workload-row" key={row.borough}>
                  <span>{titleCase(row.borough)}</span>
                  <div className="workload-track">
                    <i className="complaint-bar" style={{ width: `${complaintWidth}%` }} />
                    <i className="violation-bar" style={{ width: `${violationWidth}%` }} />
                  </div>
                  <strong>{row.totalOpenComplianceItemCount}</strong>
                </div>
              );
            })}
          </div>
        </article>

        <article className="panel attention-panel">
          <div className="panel-heading"><div><p>Prioritization</p><h2>Attention tiers</h2></div><span>Observed buildings</span></div>
          <div className="tier-list">
            {snapshot.attentionTiers.map((row) => (
              <div className={`tier-row tier-${row.tier.toLowerCase()}`} key={row.tier}>
                <span>{row.tier}</span>
                <strong>{formatInteger(row.buildingCount)}</strong>
                <small>{((row.buildingCount / snapshot.overview.observedBuildingCount) * 100).toFixed(row.buildingCount < 10 ? 2 : 1)}%</small>
              </div>
            ))}
          </div>
          <p className="method-note">The score ranks review workload. It is not a structural-safety or legal-risk determination.</p>
        </article>
      </section>

      <article className="panel priority-panel">
        <div className="panel-heading"><div><p>Investigation queue</p><h2>Priority buildings</h2></div><span>Score, unresolved items, and age</span></div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Building</th><th>BIN</th><th>Tier</th><th className="number">Score</th><th className="number">Open items</th><th className="number">Oldest item</th></tr></thead>
            <tbody>
              {filteredBuildings.length ? filteredBuildings.slice(0, 8).map((row) => (
                <tr key={row.bin}>
                  <td><strong>{row.displayAddress}</strong><small>{titleCase(row.borough)}</small></td>
                  <td>{row.bin}</td>
                  <td><span className={`status status-${row.attentionTier.toLowerCase()}`}>{row.attentionTier}</span></td>
                  <td className="number">{row.attentionScore}</td>
                  <td className="number">{row.totalOpenComplianceItemCount}</td>
                  <td className="number">{formatInteger(row.oldestOpenItemAgeDays)} days</td>
                </tr>
              )) : <tr><td className="empty-cell" colSpan={6}>No HIGH or MODERATE buildings are present in the selected bounded slice.</td></tr>}
            </tbody>
          </table>
        </div>
      </article>
    </>
  );
}

function BuildingExplorer() {
  const [query, setQuery] = useState('');
  const [selectedBin, setSelectedBin] = useState(snapshot.priorityBuildings[0].bin);
  const buildings = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return snapshot.priorityBuildings;
    return snapshot.priorityBuildings.filter((row) =>
      `${row.bin} ${row.displayAddress} ${row.borough}`.toLowerCase().includes(normalized),
    );
  }, [query]);
  const selected = snapshot.priorityBuildings.find((row) => row.bin === selectedBin)
    ?? buildings[0]
    ?? snapshot.priorityBuildings[0];

  return (
    <section className="explorer-grid">
      <article className="panel explorer-list">
        <label htmlFor="building-search">Search the priority queue</label>
        <input id="building-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Address, BIN, or borough" />
        <div className="building-options" aria-label="Priority buildings">
          {buildings.map((row) => (
            <button type="button" className={row.bin === selected.bin ? 'selected' : ''} onClick={() => setSelectedBin(row.bin)} key={row.bin}>
              <span><strong>{row.displayAddress}</strong><small>BIN {row.bin} · {titleCase(row.borough)}</small></span>
              <span className={`status status-${row.attentionTier.toLowerCase()}`}>{row.attentionScore}</span>
            </button>
          ))}
          {!buildings.length && <p className="no-results">No building matches this search.</p>}
        </div>
      </article>

      <article className="panel building-detail" aria-live="polite">
        <div className="building-title">
          <div><p>Selected building</p><h2>{selected.displayAddress}</h2><span>BIN {selected.bin} · {titleCase(selected.borough)}</span></div>
          <span className={`status status-${selected.attentionTier.toLowerCase()}`}>{selected.attentionTier}</span>
        </div>
        <div className="detail-metrics">
          <div><span>Attention score</span><strong>{selected.attentionScore}<em>/100</em></strong></div>
          <div><span>Open complaints</span><strong>{selected.openComplaintCount}</strong></div>
          <div><span>Open violations</span><strong>{selected.openViolationCount}</strong></div>
          <div><span>Oldest open item</span><strong>{formatInteger(selected.oldestOpenItemAgeDays)}<em> days</em></strong></div>
        </div>
        <div className="score-explanation">
          <p>Why this building is prioritized</p>
          <ul>
            <li>{selected.totalOpenComplianceItemCount} unresolved compliance record{selected.totalOpenComplianceItemCount === 1 ? '' : 's'} in the retained source slice.</li>
            <li>The oldest retained open item is more than one year old, activating the maximum age bonus.</li>
            <li>The score is transparent workload triage and does not infer violation severity.</li>
          </ul>
        </div>
      </article>
    </section>
  );
}

function DataQuality() {
  return (
    <>
      <section className="quality-grid">
        {snapshot.quality.map((row) => (
          <article className="quality-card" key={row.domain}>
            <div><span>{row.domain === 'permit_records' ? 'Permit records' : titleCase(row.domain)}</span><strong className={`quality-${row.qualityStatus.toLowerCase()}`}>{row.qualityStatus}</strong></div>
            <p><b>{row.buildingKeyCoveragePct.toFixed(2)}%</b> building-key coverage</p>
            <div className="coverage-track" role="progressbar" aria-valuenow={row.buildingKeyCoveragePct} aria-valuemin={0} aria-valuemax={100} aria-label={`${row.domain} building-key coverage`}><i style={{ width: `${row.buildingKeyCoveragePct}%` }} /></div>
            <small>{formatInteger(row.totalRecordCount)} retained source records</small>
          </article>
        ))}
      </section>

      <section className="quality-detail-grid">
        <article className="panel evidence-panel">
          <div className="panel-heading"><div><p>Release evidence</p><h2>Latest BI mart build</h2></div><span>Snowflake + dbt</span></div>
          <div className="evidence-list">
            <div><span>Consumption models built</span><strong>{snapshot.metadata.buildEvidence.modelsBuilt}</strong></div>
            <div><span>Model and data checks passed</span><strong>{snapshot.metadata.buildEvidence.checksPassed}</strong></div>
            <div><span>Warnings</span><strong>{snapshot.metadata.buildEvidence.warnings}</strong></div>
            <div><span>Errors</span><strong>{snapshot.metadata.buildEvidence.errors}</strong></div>
          </div>
        </article>
        <article className="panel scope-panel">
          <div className="panel-heading"><div><p>Interpretation boundary</p><h2>What this snapshot represents</h2></div></div>
          <p>{snapshot.metadata.scope}</p>
          <p>{snapshot.metadata.normalizationNote}</p>
          <div className="source-counts">
            <span>Permits <b>{formatInteger(snapshot.metadata.sourceRecords.permits)}</b></span>
            <span>Complaints <b>{formatInteger(snapshot.metadata.sourceRecords.complaints)}</b></span>
            <span>Violations <b>{formatInteger(snapshot.metadata.sourceRecords.violations)}</b></span>
          </div>
        </article>
      </section>
    </>
  );
}

export default function Home() {
  const [view, setView] = useState<View>('overview');
  const [borough, setBorough] = useState('ALL');
  const copy = viewCopy[view];

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">NY</span><span><strong>Compliance 360</strong><small>NYC DOB Analytics</small></span></div>
        <nav aria-label="Dashboard sections">
          {(['overview', 'buildings', 'quality'] as View[]).map((item) => (
            <button type="button" className={view === item ? 'nav-item active' : 'nav-item'} onClick={() => setView(item)} aria-current={view === item ? 'page' : undefined} key={item}>
              <span className="nav-code">{item === 'overview' ? '01' : item === 'buildings' ? '02' : '03'}</span>
              {item === 'overview' ? 'Overview' : item === 'buildings' ? 'Building explorer' : 'Data quality'}
            </button>
          ))}
        </nav>
        <div className="data-product"><span>Published data product</span><strong>DEV_MARTS</strong><small>Snapshot {snapshot.metadata.snapshotDate}</small></div>
        <p className="source-note">Official NYC Open Data<br />DOB NOW permits<br />DOB complaints<br />BIS violations</p>
      </aside>

      <section className="workspace">
        <header className="page-header">
          <div><p className="eyebrow">{copy.eyebrow}</p><h1>{copy.title}</h1><p>{copy.description}</p></div>
          <div className="header-tools">
            {view === 'overview' && <label htmlFor="borough-filter">Borough<select id="borough-filter" value={borough} onChange={(event) => setBorough(event.target.value)}><option value="ALL">All boroughs</option>{snapshot.boroughs.map((row) => <option key={row.borough} value={row.borough}>{titleCase(row.borough)}</option>)}</select></label>}
            <div className="refresh-status"><span /> Snapshot {snapshot.metadata.snapshotDate}</div>
          </div>
        </header>
        <div className="scope-banner"><strong>Bounded evidence, not a citywide estimate.</strong> Each source contributes 1,000 public records so the portfolio remains reproducible and cost-controlled.</div>
        {view === 'overview' && <Overview boroughFilter={borough} />}
        {view === 'buildings' && <BuildingExplorer />}
        {view === 'quality' && <DataQuality />}
        <footer>NYC Building Compliance 360 · Governed metrics from dbt · Snapshot exported {snapshot.metadata.exportedOn}</footer>
      </section>
    </main>
  );
}
