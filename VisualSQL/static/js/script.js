// VisualSQL Enterprise Intelligence Client
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);
const charts = {};

// SVG Icons
const icons = {
  grid: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/></svg>',
  code: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline></svg>',
  database: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>',
  gauge: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 14l4-4"></path><path d="M3.34 19a10 10 0 1 1 17.32 0"></path><circle cx="12" cy="14" r="1.5"></circle></svg>',
  layers: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>',
  chart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>',
  file: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>',
  moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>',
  menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>',
  play: '<svg viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>',
  refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>',
  download: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>',
  sparkles: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path></svg>',
  'trending-up': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
  'upload-cloud': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><polyline points="16 16 12 12 8 16"></polyline><line x1="12" y1="12" x2="12" y2="21"></line><path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path><polyline points="16 16 12 12 8 16"></polyline></svg>'
};

function renderIcons() {
  $$('[data-icon]').forEach(el => {
    const iconName = el.dataset.icon;
    if (icons[iconName]) el.innerHTML = icons[iconName];
  });
}
renderIcons();

// Toast Notifications
function toast(message, ok = true) {
  const el = $('#toast');
  el.textContent = message;
  el.style.background = ok ? '#0f766e' : '#dc2626';
  el.style.display = 'block';
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.style.display = 'none'; }, 4000);
}

// API Fetch Utility
async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || response.statusText);
  return data;
}

const post = (url, body) => api(url, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body)
});

// Table Component
function table(columns, rows, emptyMsg = 'No records available.') {
  if (!rows || !rows.length) return `<div class="tbl-empty">${emptyMsg}</div>`;
  return `<table><thead><tr>${columns.map(c => `<th>${c}</th>`).join('')}</tr></thead><tbody>${
    rows.map(row => `<tr>${row.map(val => `<td>${val ?? ''}</td>`).join('')}</tr>`).join('')
  }</tbody></table>`;
}

// Badges
function badge(status) {
  const s = String(status || '').toLowerCase();
  const cls = (s === 'ok' || s === 'completed') ? 'status-ok' : (s === 'error' ? 'status-error' : 'status-running');
  return `<span class="status-badge ${cls}">${status || '-'}</span>`;
}

function opBadge(type, severity) {
  return `<span class="op-badge ${severity || 'info'}">${type || 'UNKNOWN'}</span>`;
}

// Chart Helper
function createOrUpdateChart(id, type, labels, datasets, options = {}) {
  if (typeof Chart === 'undefined') return;
  const canvas = $(id);
  if (!canvas) return;

  if (charts[id]) {
    charts[id].destroy();
  }

  const isDark = document.documentElement.dataset.theme === 'dark';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: datasets.length > 1,
        labels: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11, weight: '600' } }
      },
      tooltip: {
        backgroundColor: isDark ? '#1e293b' : '#ffffff',
        titleColor: isDark ? '#ffffff' : '#0f172a',
        bodyColor: isDark ? '#cbd5e1' : '#334155',
        borderColor: isDark ? '#334155' : '#e2e8f0',
        borderWidth: 1,
        padding: 10,
        boxPadding: 4,
        usePointStyle: true
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: textColor, font: { family: 'Plus Jakarta Sans', size: 11 } }
      },
      y: {
        beginAtZero: true,
        grid: { color: gridColor },
        ticks: { color: textColor, font: { family: 'JetBrains Mono', size: 10 } }
      }
    }
  };

  charts[id] = new Chart(canvas, {
    type,
    data: { labels, datasets },
    options: { ...defaultOptions, ...options }
  });
}

// 1. System Status & Schema Explorer
async function loadStatus() {
  try {
    const s = await api('/api/status');
    const isSqlite = s.backend === 'sqlite';
    $('#backend-label').textContent = isSqlite ? 'SQLite Engine' : 'MySQL 8.0';
    $('#backend-meta').textContent = `${s.tables_count || 0} tables • WAL Mode`;
    $('#topbar-backend').textContent = isSqlite ? 'SQLite Engine (WAL)' : 'MySQL 8.0';
    $('#topbar-records').textContent = (s.total_records || 0).toLocaleString();
    $('#topbar-tables').textContent = s.tables_count || 0;
  } catch (err) {
    $('#backend-label').textContent = 'Engine Offline';
    $('#backend-meta').textContent = 'Connection error';
  }
}

async function loadSchema() {
  const container = $('#schema-tree');
  try {
    const data = await api('/api/schema');
    const tables = data.tables || [];
    if (!tables.length) {
      container.innerHTML = '<div class="schema-loading">No tables found. Click Seed Data.</div>';
      return;
    }

    container.innerHTML = tables.map(t => `
      <div class="schema-table-item" data-table="${t.name}">
        <div class="schema-table-header" onclick="toggleSchemaTable(this)">
          <span><strong>${t.name}</strong></span>
          <span class="schema-table-badge">${(t.row_count || 0).toLocaleString()} rows</span>
        </div>
        <div class="schema-columns-list">
          ${t.columns.map(c => `
            <div class="schema-col-item" onclick="insertColumnToEditor('${c.name}')" title="Click to insert">
              <span>${c.name} ${c.pk ? '<span class="schema-col-pk">PK</span>' : ''}</span>
              <span class="schema-col-type">${c.type}</span>
            </div>
          `).join('')}
          <div style="margin-top: 6px; padding-top: 6px; border-top: 1px dashed var(--border);">
            <button class="btn-text-tool" onclick="queryTableSample('${t.name}')">Select Top 50</button>
          </div>
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="schema-loading" style="color:var(--danger)">Failed to load schema: ${err.message}</div>`;
  }
}

window.toggleSchemaTable = function(header) {
  header.parentElement.classList.toggle('open');
};

window.insertColumnToEditor = function(colName) {
  const editor = $('#sql');
  editor.value += ` ${colName}`;
  editor.focus();
};

window.queryTableSample = function(tblName) {
  $('#sql').value = `SELECT * FROM ${tblName} LIMIT 50`;
  runQuery();
};

// Filter schema tree
$('#schema-filter')?.addEventListener('input', (e) => {
  const term = e.target.value.toLowerCase();
  $$('.schema-table-item').forEach(item => {
    const text = item.textContent.toLowerCase();
    item.style.display = text.includes(term) ? 'block' : 'none';
  });
});

// 2. Dashboard Analytics
async function loadDash() {
  try {
    const [summary, results, history] = await Promise.all([
      api('/api/summary'),
      api('/api/results'),
      api('/api/history')
    ]);

    // KPI Cards
    $('#kpi-experiments').textContent = summary.experiments || 0;
    $('#kpi-experiments-sub').textContent = `${history.length} audit logs stored`;
    $('#kpi-queries').textContent = summary.queries || 0;
    $('#kpi-queries-sub').textContent = `Across ${summary.total_datasets || 0} dataset scales`;
    $('#kpi-avg-ms').textContent = summary.avg_ms != null ? `${summary.avg_ms.toFixed(2)} ms` : '-';
    $('#kpi-best-gain').textContent = summary.best_improvement != null ? `+${summary.best_improvement.toFixed(1)}%` : '-';
    $('#kpi-best-config').textContent = summary.best_config ? `Fastest: ${summary.best_config}` : 'Benchmark baseline';

    $('#nav-exp-count').textContent = summary.experiments || 0;
    $('#nav-ds-count').textContent = summary.total_datasets || 0;

    // Recent Feed
    if (results && results.length) {
      const topRuns = results.slice(0, 8);
      $('#dash-recent-tbl').innerHTML = table(
        ['ID', 'Experiment', 'Scale', 'Config', 'Index Used', 'Mean Latency', 'Gain %', 'Access Type', 'Report'],
        topRuns.map(r => [
          `#${r.id}`,
          `<strong>${r.query_name}</strong>`,
          `${(r.dataset_size || 0).toLocaleString()} rows`,
          r.config,
          `<code>${r.index_config}</code>`,
          `${(r.avg_ms || 0).toFixed(2)} ms`,
          r.improvement_pct != null ? `<span style="color:var(--success);font-weight:700">+${r.improvement_pct.toFixed(1)}%</span>` : '-',
          opBadge(r.access_type || 'SCAN', (r.access_type || '').includes('INDEX') ? 'success' : 'danger'),
          `<a class="btn-text-tool" href="/report/pdf/${r.id}">PDF</a>`
        ])
      );

      // Latency Chart
      const latest = results.slice(0, 8).reverse();
      createOrUpdateChart(
        '#c-dash-latency',
        'bar',
        latest.map(x => `${x.config} (${(x.dataset_size/1000)}k)`),
        [{
          label: 'Average Latency (ms)',
          data: latest.map(x => x.avg_ms || 0),
          backgroundColor: latest.map(x => (x.config.includes('index') ? '#0f766e' : '#2563eb')),
          borderRadius: 6
        }]
      );

      // Gain Distribution
      createOrUpdateChart(
        '#c-dash-gain',
        'bar',
        latest.map(x => `${x.config} #${x.id}`),
        [{
          label: 'Improvement %',
          data: latest.map(x => Math.max(0, x.improvement_pct || 0)),
          backgroundColor: '#16a34a',
          borderRadius: 6
        }],
        { indexAxis: 'y' }
      );
    } else {
      $('#dash-recent-tbl').innerHTML = '<div class="tbl-empty">No benchmarks recorded yet. Run your first benchmark to populate live analytics.</div>';
    }

    // Scalability Simulation Curve (O(N) vs O(log N))
    renderScalabilityCurve();

  } catch (err) {
    toast(`Dashboard error: ${err.message}`, false);
  }
}

function renderScalabilityCurve() {
  const scales = ['1k rows', '10k rows', '50k rows', '100k rows'];
  const fullScanSim = [0.45, 4.2, 21.5, 43.8];
  const indexSeekSim = [0.08, 0.11, 0.14, 0.17];

  createOrUpdateChart(
    '#c-dash-scale',
    'line',
    scales,
    [
      {
        label: 'Full Table Scan O(N)',
        data: fullScanSim,
        borderColor: '#dc2626',
        backgroundColor: 'rgba(220, 38, 38, 0.08)',
        fill: true,
        tension: 0.35,
        borderWidth: 2.5
      },
      {
        label: 'B-Tree Index Seek O(log N)',
        data: indexSeekSim,
        borderColor: '#0f766e',
        backgroundColor: 'rgba(15, 118, 110, 0.1)',
        fill: true,
        tension: 0.2,
        borderWidth: 2.5
      }
    ]
  );
}

// 3. SQL Studio Workbench
async function runQuery() {
  const btn = $('#run-query');
  btn.disabled = true;
  btn.innerHTML = '<span data-icon="refresh"></span> Running...';
  renderIcons();

  const stats = $('#query-stats');
  stats.style.display = 'none';

  try {
    const sql = $('#sql').value.trim();
    if (!sql) throw new Error('Please enter a SQL query.');

    const size = $('#size').value;
    const res = await post('/api/query', { sql, size });

    // Update stats bar
    $('#q-stat-time').textContent = `${res.execution_time_ms} ms`;
    $('#q-stat-rows').textContent = `${res.row_count} rows ${res.limited ? '(LIMIT 200)' : ''}`;
    stats.style.display = 'flex';

    // Update results counter
    $('#results-counter').textContent = `Returned ${res.row_count} rows in ${res.execution_time_ms} ms`;

    // Render table
    $('#q-out').innerHTML = table(res.columns, res.rows, 'Query executed successfully with 0 matching rows.');

    toast(`Query completed in ${res.execution_time_ms} ms`);
  } catch (err) {
    toast(err.message, false);
    $('#q-out').innerHTML = `<div class="tbl-empty" style="color:var(--danger)">Error: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span data-icon="play"></span> Run Query <span class="kbd-shortcut">Ctrl+Enter</span>';
    renderIcons();
  }
}

async function formatQuerySql() {
  try {
    const raw = $('#sql').value.trim();
    if (!raw) return;
    const res = await post('/api/validate', { sql: raw });
    if (res.sql) {
      $('#sql').value = res.sql;
      toast('SQL formatted');
      updateIndexCandidates(res.candidate_indexes);
    }
  } catch (err) {
    toast(err.message, false);
  }
}

function updateIndexCandidates(candidates) {
  const container = $('#editor-index-chips');
  if (!candidates || !candidates.length) {
    container.innerHTML = '<span class="chip-placeholder">No high-impact index needed</span>';
    return;
  }
  container.innerHTML = candidates.map(c => `
    <span class="chip-tag" onclick="applyIndexToBenchmark('${c.join(', ')}')">
      + (${c.join(', ')})
    </span>
  `).join('');
}

window.applyIndexToBenchmark = function(cols) {
  $('#b-idx').value = cols;
  location.hash = '#bench';
  toast(`Applied index (${cols}) to Benchmark Lab`);
};

// Ctrl+Enter shortcut in SQL editor
$('#sql')?.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    runQuery();
  }
});

// Studio toolbar jumps
$('#btn-studio-explain')?.addEventListener('click', () => {
  $('#p-sql').value = $('#sql').value;
  $('#p-size').value = $('#size').value;
  location.hash = '#plan';
  runPlan();
});

$('#btn-studio-benchmark')?.addEventListener('click', () => {
  $('#b-sql').value = $('#sql').value;
  $('#b-size').value = $('#size').value;
  location.hash = '#bench';
});

// 4. Visual Execution Plan & Analyzer
async function runPlan() {
  const btn = $('#run-plan');
  btn.disabled = true;
  btn.innerHTML = '<span data-icon="refresh"></span> Analyzing Plan...';
  renderIcons();

  try {
    const sql = $('#p-sql').value.trim();
    const size = $('#p-size').value;
    const plan = await post('/api/explain', { sql, size });

    // 1. Verdict Banner
    $('#plan-verdict-box').style.display = 'block';
    const score = plan.health_score || 50;
    $('#verdict-score').textContent = score;

    const circle = $('#verdict-score-circle');
    if (score >= 85) {
      circle.style.borderColor = 'var(--success)';
      circle.style.background = 'var(--success-bg)';
      circle.style.color = 'var(--success)';
      $('#verdict-tag').textContent = 'OPTIMAL EXECUTION';
      $('#verdict-tag').style.color = 'var(--success)';
    } else if (score >= 60) {
      circle.style.borderColor = 'var(--warning)';
      circle.style.background = 'var(--warning-bg)';
      circle.style.color = 'var(--warning)';
      $('#verdict-tag').textContent = 'ACCEPTABLE';
      $('#verdict-tag').style.color = 'var(--warning)';
    } else {
      circle.style.borderColor = 'var(--danger)';
      circle.style.background = 'var(--danger-bg)';
      circle.style.color = 'var(--danger)';
      $('#verdict-tag').textContent = 'HIGH LATENCY DETECTED';
      $('#verdict-tag').style.color = 'var(--danger)';
    }

    $('#verdict-title').textContent = plan.verdict || 'Plan Analyzed';
    $('#verdict-desc').textContent = plan.steps?.[0]?.meaning || 'Database query access plan generated.';

    // 2. Visual Node Flow Graph
    const flowContainer = $('#plan-flow-container');
    $('#plan-graph-panel').style.display = 'block';

    const steps = plan.steps || [];
    flowContainer.innerHTML = steps.map((s, idx) => `
      <div class="flow-node">
        <div class="flow-node-title">Step ${s.step_id || idx+1}: ${s.table}</div>
        <div class="flow-node-main">${opBadge(s.access_type, s.severity)}</div>
        <div class="flow-node-desc">${s.key ? `Key: ${s.key}` : (s.full_scan ? 'Full Table Scan' : 'Filter Stage')}</div>
      </div>
      ${idx < steps.length - 1 ? '<div class="flow-arrow">&rarr;</div>' : ''}
    `).join('') + `
      <div class="flow-arrow">&rarr;</div>
      <div class="flow-node" style="border-color:var(--primary);background:var(--primary-light)">
        <div class="flow-node-title">Output Stage</div>
        <div class="flow-node-main">Client Result Set</div>
        <div class="flow-node-desc">Columns Projected</div>
      </div>
    `;

    // 3. Structured Steps Table
    $('#p-out').innerHTML = table(
      ['Step', 'Table', 'Operator / Access Type', 'Key Used', 'Estimated Rows', 'Details / Extra', 'Diagnostic Meaning & Tip'],
      steps.map(s => [
        `#${s.step_id}`,
        `<strong>${s.table}</strong>`,
        opBadge(s.access_type, s.severity),
        s.key ? `<code>${s.key}</code>` : '<span class="text-muted">None</span>',
        s.rows || '~',
        `<code>${s.extra || ''}</code>`,
        `<div><strong>${s.meaning}</strong></div><div style="font-size:11px;color:var(--muted);margin-top:3px">${s.suggestion || ''}</div>`
      ])
    );

    toast('Execution plan generated');
  } catch (err) {
    toast(err.message, false);
    $('#p-out').innerHTML = `<div class="tbl-empty" style="color:var(--danger)">Error: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span data-icon="layers"></span> Analyze Execution Plan';
    renderIcons();
  }
}

// 5. Benchmark Lab
async function runBench() {
  const btn = $('#b-go');
  btn.disabled = true;
  btn.innerHTML = '<span data-icon="refresh"></span> Running Multi-Pass Benchmark...';
  renderIcons();

  try {
    const name = $('#b-name').value.trim() || 'Benchmark Run';
    const sql = $('#b-sql').value.trim();
    const size = $('#b-size').value;
    const reps = $('#b-reps').value;
    const idxRaw = $('#b-idx').value.trim();
    const indexCols = idxRaw ? idxRaw.split(',').map(s => s.trim()).filter(Boolean) : null;

    const data = await post('/api/benchmark', {
      name, sql, size, reps, index_cols: indexCols
    });

    const expId = data.experiment_id;
    const results = data.results || [];
    const recs = data.recommendations || [];

    // Format output container
    $('#b-out').innerHTML = `
      <div class="panel">
        <div class="panel-head">
          <div>
            <h3>Experiment #${expId}: ${name}</h3>
            <p class="panel-subtitle">Evaluated on ${(parseInt(size)).toLocaleString()} records with ${reps} repetition passes</p>
          </div>
          <div class="toolbar">
            <a class="button button-secondary button-sm" href="/report/pdf/${expId}">
              <span data-icon="download"></span> Download Executive PDF
            </a>
            <a class="button button-secondary button-sm" href="/report/csv?experiment=${expId}">
              <span data-icon="download"></span> Export CSV
            </a>
          </div>
        </div>

        <!-- Comparison Bar Chart -->
        <div class="chart-wrap" style="height: 250px; margin-bottom: 20px;">
          <canvas id="c-bench-result"></canvas>
        </div>

        <!-- Metrics Table -->
        ${table(
          ['Configuration', 'Index Applied', 'Mean (ms)', 'Median', 'Min', 'Max', 'P95', 'Rows', 'Gain %', 'Access', 'Status'],
          results.map(r => [
            `<strong>${r.config}</strong>`,
            `<code>${(r.index || []).join(', ') || 'none'}</code>`,
            `<strong>${(r.avg || 0).toFixed(2)} ms</strong>`,
            `${(r.median || r.avg || 0).toFixed(2)}`,
            `${(r.min || 0).toFixed(2)}`,
            `${(r.max || 0).toFixed(2)}`,
            `${(r.p95 || r.max || 0).toFixed(2)}`,
            r.rows || 0,
            r.improvement != null ? `
              <div>
                <strong style="color:var(--success)">+${r.improvement.toFixed(1)}%</strong>
                <div class="progress-bar-wrap">
                  <div class="progress-bar-fill" style="width:${Math.min(100, Math.max(0, r.improvement))}%"></div>
                </div>
              </div>
            ` : '-',
            opBadge(r.access_type || 'SCAN', (r.access_type || '').includes('INDEX') ? 'success' : 'danger'),
            badge(r.status)
          ])
        )}

        <!-- Recommendations Box -->
        <div class="recommendations-box">
          <h4>Optimization Insights & DBA Recommendations</h4>
          <ul>
            ${recs.map(rec => `<li>${rec.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</li>`).join('')}
          </ul>
        </div>
      </div>
    `;

    renderIcons();

    // Render Benchmark Chart
    createOrUpdateChart(
      '#c-bench-result',
      'bar',
      results.map(r => r.config),
      [{
        label: 'Execution Latency (ms)',
        data: results.map(r => r.avg || 0),
        backgroundColor: results.map(r => r.config.includes('index') ? '#0f766e' : (r.config.includes('rewrite') ? '#0284c7' : '#e11d48')),
        borderRadius: 6
      }]
    );

    toast(`Benchmark #${expId} completed!`);
    loadStatus();
  } catch (err) {
    toast(err.message, false);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span data-icon="play"></span> Run Benchmark Experiment';
    renderIcons();
  }
}

// 6. Analytics Results Matrix
async function loadResultsMatrix() {
  try {
    const results = await api('/api/results');
    $('#r-tbl').innerHTML = table(
      ['ID', 'Workload Name', 'Dataset Scale', 'Configuration', 'Index Setup', 'Mean (ms)', 'Min', 'Max', 'Gain %', 'Access Type', 'Status'],
      results.map(r => [
        `#${r.id}`,
        r.query_name,
        `${(r.dataset_size || 0).toLocaleString()} rows`,
        `<strong>${r.config}</strong>`,
        `<code>${r.index_config}</code>`,
        `<strong>${(r.avg_ms || 0).toFixed(2)} ms</strong>`,
        `${(r.min_ms || 0).toFixed(2)}`,
        `${(r.max_ms || 0).toFixed(2)}`,
        r.improvement_pct != null ? `<span style="color:var(--success);font-weight:700">+${r.improvement_pct.toFixed(1)}%</span>` : '-',
        opBadge(r.access_type || 'SCAN', (r.access_type || '').includes('INDEX') ? 'success' : 'danger'),
        badge(r.status)
      ])
    );

    if (results.length) {
      const top12 = results.slice(0, 12).reverse();
      createOrUpdateChart(
        '#c-matrix-latency',
        'bar',
        top12.map(x => `${x.config} (${(x.dataset_size/1000)}k)`),
        [{
          label: 'Latency (ms)',
          data: top12.map(x => x.avg_ms || 0),
          backgroundColor: '#0f766e',
          borderRadius: 6
        }]
      );

      createOrUpdateChart(
        '#c-matrix-gain',
        'bar',
        top12.map(x => `${x.config} #${x.id}`),
        [{
          label: 'Gain %',
          data: top12.map(x => Math.max(0, x.improvement_pct || 0)),
          backgroundColor: '#16a34a',
          borderRadius: 6
        }],
        { indexAxis: 'y' }
      );
    }
  } catch (err) {
    toast(err.message, false);
  }
}

// 7. Datasets & Data Factory
async function loadDatasets() {
  try {
    const ds = await api('/api/datasets');
    $('#ds-list').innerHTML = table(
      ['Table Name', 'Row Count', 'Source', 'Created At', 'Actions'],
      ds.map(d => [
        `<strong>${d.table_name}</strong>`,
        `${(d.row_count || 0).toLocaleString()} records`,
        `<span class="status-badge status-ok">${d.source}</span>`,
        d.created_at,
        `<button class="btn-text-tool" onclick="deleteDataset('${d.table_name}')" style="color:var(--danger)">Delete</button>`
      ])
    );
  } catch (err) {
    toast(err.message, false);
  }
}

window.deleteDataset = async function(tblName) {
  if (!confirm(`Are you sure you want to drop table '${tblName}'?`)) return;
  try {
    await api(`/api/datasets/${tblName}`, { method: 'DELETE' });
    toast(`Dataset ${tblName} dropped`);
    loadDatasets();
    loadSchema();
    loadStatus();
  } catch (err) {
    toast(err.message, false);
  }
};

async function setupStandardData() {
  toast('Synthesizing standard benchmark datasets (1k, 10k, 50k, 100k)...');
  try {
    await post('/api/datasets/setup', {});
    toast('Benchmark datasets generated successfully!');
    loadDatasets();
    loadSchema();
    loadStatus();
  } catch (err) {
    toast(err.message, false);
  }
}

async function customGenerateData() {
  const size = $('#gen-size').value;
  const name = $('#gen-name').value.trim();
  toast(`Generating ${size} records into ${name}...`);
  try {
    await post('/api/datasets/generate', { size, name });
    toast(`Dataset '${name}' created!`);
    loadDatasets();
    loadSchema();
    loadStatus();
  } catch (err) {
    toast(err.message, false);
  }
}

// CSV Upload & Preview
function getCsvFormData() {
  const fileInput = $('#csv');
  if (!fileInput.files[0]) throw new Error('Please select a CSV file first.');
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  form.append('name', $('#dname').value.trim() || 'custom_upload');
  return form;
}

$('#drop-zone')?.addEventListener('click', () => $('#csv').click());

$('#csv')?.addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (f) {
    $('#file-chosen-name').textContent = `Selected: ${f.name} (${(f.size/1024).toFixed(1)} KB)`;
  }
});

async function previewCsv() {
  try {
    const res = await api('/api/datasets/preview', { method: 'POST', body: getCsvFormData() });
    const rows = res.rows || [];
    const cols = Object.keys(rows[0] || {});
    $('#prev').innerHTML = table(cols, rows.map(r => cols.map(c => r[c])));
    toast('CSV preview loaded');
  } catch (err) {
    toast(err.message, false);
  }
}

async function uploadCsv() {
  try {
    toast('Importing CSV dataset...');
    await api('/api/datasets/upload', { method: 'POST', body: getCsvFormData() });
    toast('Dataset imported successfully!');
    $('#prev').innerHTML = '';
    loadDatasets();
    loadSchema();
    loadStatus();
  } catch (err) {
    toast(err.message, false);
  }
}

// 8. Audit History
async function loadHistory() {
  try {
    const hist = await api('/api/history');
    $('#h-tbl').innerHTML = table(
      ['ID', 'Workload Name', 'Dataset Scale', 'Repetitions', 'Status', 'Timestamp', 'Export Reports', 'Actions'],
      hist.map(h => [
        `#${h.id}`,
        `<strong>${h.query_name}</strong>`,
        `${(h.dataset_size || 0).toLocaleString()} rows`,
        `${h.repetitions} passes`,
        badge(h.status),
        h.created_at,
        `<a class="btn-text-tool" href="/report/pdf/${h.id}">PDF</a> &bull; <a class="btn-text-tool" href="/report/csv?experiment=${h.id}">CSV</a>`,
        `<button class="btn-text-tool" onclick="deleteHistoryItem(${h.id})" style="color:var(--danger)">Delete</button>`
      ])
    );
  } catch (err) {
    toast(err.message, false);
  }
}

window.deleteHistoryItem = async function(id) {
  if (!confirm(`Delete experiment #${id}?`)) return;
  try {
    await api(`/api/history/${id}`, { method: 'DELETE' });
    toast(`Experiment #${id} deleted`);
    loadHistory();
    loadDash();
  } catch (err) {
    toast(err.message, false);
  }
};

$('#btn-clear-history')?.addEventListener('click', async () => {
  if (!confirm('Are you sure you want to clear all benchmark history and results?')) return;
  try {
    await post('/api/history/clear', {});
    toast('History cleared');
    loadHistory();
    loadDash();
  } catch (err) {
    toast(err.message, false);
  }
});

// Navigation & Page Switching
const pageTitles = {
  dashboard: 'Overview Dashboard',
  editor: 'SQL Studio & Workbench',
  plan: 'Visual Execution Plan',
  bench: 'Benchmark Studio',
  results: 'Performance Analytics Matrix',
  datasets: 'Data Factory & Management',
  history: 'Audit History',
  reports: 'Reports & Exports'
};

function navigate() {
  const hash = (location.hash || '#dashboard').slice(1);
  const activeId = pageTitles[hash] ? hash : 'dashboard';

  $$('section').forEach(s => s.classList.toggle('on', s.id === activeId));
  $$('[data-nav]').forEach(link => link.classList.toggle('on', link.dataset.nav === activeId));
  $('#page-title').textContent = pageTitles[activeId];

  $('.sidebar')?.classList.remove('open');

  // Trigger page loaders
  if (activeId === 'dashboard') loadDash();
  else if (activeId === 'editor') { loadSchema(); }
  else if (activeId === 'plan') { /* plan page */ }
  else if (activeId === 'bench') { /* bench page */ }
  else if (activeId === 'results') loadResultsMatrix();
  else if (activeId === 'datasets') loadDatasets();
  else if (activeId === 'history') loadHistory();
}

// Theme Toggle
$('#theme')?.addEventListener('click', () => {
  const current = document.documentElement.dataset.theme;
  const next = current === 'dark' ? '' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem('theme', next);
  // Re-render active charts to pick up color palette
  navigate();
});
document.documentElement.dataset.theme = localStorage.getItem('theme') || '';

// Event Bindings
$('#menu-button')?.addEventListener('click', () => $('.sidebar').classList.toggle('open'));
$('#btn-refresh-dash')?.addEventListener('click', loadDash);
$('#btn-quick-seed')?.addEventListener('click', setupStandardData);
$('#btn-refresh-schema')?.addEventListener('click', loadSchema);

$('#q-lib')?.addEventListener('change', (e) => {
  $('#sql').value = e.target.value;
  formatQuerySql();
});

$('#run-query')?.addEventListener('click', runQuery);
$('#btn-format-sql')?.addEventListener('click', formatQuerySql);
$('#run-plan')?.addEventListener('click', runPlan);
$('#b-go')?.addEventListener('click', runBench);
$('#setup-data')?.addEventListener('click', setupStandardData);
$('#btn-custom-generate')?.addEventListener('click', customGenerateData);
$('#preview-csv')?.addEventListener('click', previewCsv);
$('#upload-csv')?.addEventListener('click', uploadCsv);

// Init
window.addEventListener('hashchange', navigate);
navigate();
loadStatus();
loadSchema();
loadDash();
