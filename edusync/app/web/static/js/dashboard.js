/* EduSynC AICTE Directorate dashboard. */
(function () {
  'use strict';

  const api = window.EduSync.api;
  const escapeHtml = window.EduSync.escapeHtml;
  const formatNumber = window.EduSync.formatNumber;

  function setText(id, value) {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  }

  async function loadKpis() {
    const response = await api('/api/dashboard/national');
    if (!response.ok) return;
    const kpi = await response.json();
    setText('k-institutions', formatNumber(kpi.institution_count));
    setText('k-programmes', formatNumber(kpi.programme_count));
    setText('k-enrolled', formatNumber(kpi.total_enrolled));
    setText('k-anomalies', formatNumber(kpi.flagged_anomalies));
    setText('k-utilisation', kpi.utilisation_percent + '% of sanctioned intake');
    setText('k-critical', formatNumber(kpi.critical_anomalies) + ' critical');
  }

  async function loadIntake() {
    const response = await api('/api/dashboard/intake');
    if (!response.ok) return;
    const rows = await response.json();
    const body = document.getElementById('intake-rows');
    body.innerHTML = '';
    rows.forEach(function (row) {
      const tr = document.createElement('tr');
      const utilisation = row.utilisation_percent;
      tr.innerHTML =
        '<td>' + escapeHtml(row.institution_name || row.institution_id) + '</td>' +
        '<td>' + escapeHtml(row.program_name) + ' <span class="mono muted">' + escapeHtml(row.program_id) + '</span></td>' +
        '<td>' + formatNumber(row.approved_intake) + '</td>' +
        '<td>' + formatNumber(row.total_enrolled) + '</td>' +
        '<td style="min-width:150px"><div class="bar' + (row.has_breach ? ' over' : '') + '">' +
        '<span style="width:' + Math.min(utilisation, 100) + '%"></span></div>' +
        '<span class="mono muted">' + utilisation + '%</span></td>' +
        '<td>' + formatNumber(row.nri_enrolled + row.oci_fn_enrolled + row.tfw_enrolled + row.pmsss_enrolled) + '</td>' +
        '<td>' + (row.has_breach ? '<span class="badge HIGH">Breach</span>' : '<span class="badge VERIFIED">Within cap</span>') + '</td>';
      body.appendChild(tr);
    });
  }

  async function loadCompliance() {
    const response = await api('/api/dashboard/compliance');
    if (!response.ok) return;
    const rows = await response.json();
    const body = document.getElementById('compliance-rows');
    body.innerHTML = '';
    rows.forEach(function (row) {
      const tr = document.createElement('tr');
      const band = row.risk_band === 'CRITICAL' ? 'CRITICAL_RISK' : (row.risk_band === 'HIGH' ? 'HIGH_RISK' : row.risk_band);
      tr.innerHTML =
        '<td>' + escapeHtml(row.institution_name) + '</td>' +
        '<td>' + escapeHtml(row.state) + '</td>' +
        '<td>' + formatNumber(row.total_approved) + '</td>' +
        '<td>' + formatNumber(row.total_enrolled) + '</td>' +
        '<td>' + (row.utilisation * 100).toFixed(1) + '%</td>' +
        '<td>' + formatNumber(row.breaches) + '</td>' +
        '<td><span class="badge ' + band + '">' + escapeHtml(row.risk_band) + '</span> ' + row.risk_score + '</td>';
      body.appendChild(tr);
    });
  }

  async function loadRisk() {
    const response = await api('/api/dashboard/risk');
    if (!response.ok) return;
    const rows = await response.json();
    const container = document.getElementById('risk-cards');
    container.innerHTML = '';
    if (!rows.length) {
      container.innerHTML = '<div class="card"><p>No institution currently carries an anomaly.</p></div>';
      return;
    }
    rows.forEach(function (risk) {
      const band = risk.band === 'CRITICAL' ? 'CRITICAL_RISK' : (risk.band === 'HIGH' ? 'HIGH_RISK' : risk.band);
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML =
        '<div class="pill-row"><h3 style="margin:0">' + escapeHtml(risk.institution_id) + '</h3>' +
        '<span class="badge ' + band + '">' + escapeHtml(risk.band) + '</span>' +
        '<span class="mono">' + risk.score + ' / 100</span></div>' +
        '<p style="margin-top:8px">' + risk.reasons.map(escapeHtml).join(' ') + '</p>' +
        '<p class="hint" style="margin-top:8px">Families: ' + risk.families.map(escapeHtml).join(', ') + '</p>';
      container.appendChild(card);
    });
  }

  async function loadAll() {
    await Promise.all([loadKpis(), loadIntake(), loadCompliance(), loadRisk()]);
  }

  document.querySelectorAll('.tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      document.querySelectorAll('.tab').forEach(function (other) { other.classList.remove('active'); });
      tab.classList.add('active');
      ['intake', 'compliance', 'risk'].forEach(function (view) {
        const section = document.getElementById('view-' + view);
        if (section) section.hidden = view !== tab.dataset.view;
      });
    });
  });

  document.getElementById('refresh-btn').addEventListener('click', loadAll);

  loadAll();
  setInterval(loadAll, 30000);
})();
