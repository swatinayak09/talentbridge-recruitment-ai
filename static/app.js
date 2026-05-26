const API = "";

let requisitions = [];
let combinedData = null;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

async function fetchJSON(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function healthClass(value, thresholds) {
  if (value >= thresholds.critical) return "critical";
  if (value >= thresholds.warning) return "warning";
  return "";
}

function severityBadge(sev) {
  const map = { critical: "badge-critical", high: "badge-high", medium: "badge-medium", low: "badge-low" };
  return `<span class="badge ${map[sev] || "badge-low"}">${sev}</span>`;
}

function healthBadge(h) {
  const labels = { healthy: "Healthy", watch: "Watch", at_risk: "At Risk", critical: "Critical" };
  const cls = h === "healthy" ? "badge-healthy" : h === "watch" ? "badge-watch" : "badge-at_risk";
  return `<span class="badge ${cls}">${labels[h] || h}</span>`;
}

function renderMetrics(pipeline, escalation) {
  const m = pipeline.metrics;
  const em = escalation.metrics;
  $("#metrics-row").innerHTML = `
    <div class="metric-card">
      <div class="metric-label">Active Candidates</div>
      <div class="metric-value">${m.total_candidates}</div>
      <div class="metric-sub">${m.open_requisitions} open roles</div>
    </div>
    <div class="metric-card warning">
      <div class="metric-label">SLA Breach Rate</div>
      <div class="metric-value">${m.sla_breach_rate_pct}%</div>
      <div class="metric-sub">Avg ${m.avg_days_in_stage} days in stage</div>
    </div>
    <div class="metric-card ${m.roles_at_risk > 0 ? "critical" : ""}">
      <div class="metric-label">Roles at Risk</div>
      <div class="metric-value">${m.roles_at_risk}</div>
      <div class="metric-sub">Pipeline health alert</div>
    </div>
    <div class="metric-card ${em.critical_count > 0 ? "critical" : ""}">
      <div class="metric-label">Escalations</div>
      <div class="metric-value">${em.total_escalations}</div>
      <div class="metric-sub">${em.critical_count} critical · ${em.on_hold_count} on hold</div>
    </div>
  `;
}

function renderStageDistribution(dist) {
  const max = Math.max(...Object.values(dist), 1);
  const rows = Object.entries(dist)
    .map(
      ([stage, count]) => `
    <div class="stage-bar-row">
      <span>${stage}</span>
      <div class="stage-bar-track"><div class="stage-bar-fill" style="width:${(count / max) * 100}%"></div></div>
      <span>${count}</span>
    </div>`
    )
    .join("");
  $("#stage-distribution").innerHTML = rows || '<p class="empty-state">No data</p>';
}

function renderBottlenecks(bottlenecks) {
  const el = $("#bottlenecks-list");
  if (!bottlenecks.length) {
    el.innerHTML = '<p class="empty-state">No bottlenecks detected</p>';
    return;
  }
  el.innerHTML = `<ul class="item-list">${bottlenecks
    .map(
      (b) => `
    <li>
      <div class="item-title">${severityBadge(b.severity)} ${b.message}</div>
      <div class="item-action">→ ${b.recommendation}</div>
    </li>`
    )
    .join("")}</ul>`;
}

function renderAging(aging) {
  const el = $("#aging-list");
  if (!aging.length) {
    el.innerHTML = '<p class="empty-state">No aging applications</p>';
    return;
  }
  el.innerHTML = `<ul class="item-list">${aging
    .map(
      (a) => `
    <li>
      <div class="item-title">${a.candidate_name} — ${a.role_title}</div>
      <div class="item-meta">${a.stage} · ${a.days_in_stage} days (${a.days_over_sla} over SLA) · ${a.recruiter}</div>
      <div class="item-action">${a.pending_action}</div>
    </li>`
    )
    .join("")}</ul>`;
}

function renderRoleTable(roles) {
  const el = $("#role-table-body");
  el.innerHTML = roles
    .map(
      (r) => `
    <tr>
      <td><strong>${r.title}</strong><br><span style="color:var(--gray-500);font-size:0.75rem">${r.requisition_id}</span></td>
      <td>${r.client || "—"}</td>
      <td>${r.candidate_count}</td>
      <td>${healthBadge(r.health)}</td>
      <td>${r.recruiter}</td>
      <td>${r.oldest_in_stage_days}d</td>
    </tr>`
    )
    .join("");
}

function renderPriorityActions(actions) {
  const el = $("#priority-actions");
  if (!actions.length) {
    el.innerHTML = '<p class="empty-state">No pending actions</p>';
    return;
  }
  el.innerHTML = `<ul class="item-list">${actions
    .slice(0, 8)
    .map(
      (a) => `
    <li>
      <div class="item-title">${severityBadge(a.urgency === "high" ? "high" : "low")} ${a.candidate_name} · ${a.role_title}</div>
      <div class="item-action">${a.action} <span style="color:var(--gray-500)">— ${a.owner}</span></div>
    </li>`
    )
    .join("")}</ul>`;
}

function renderPipelinePanel(pipeline) {
  $("#pipeline-summary").textContent = pipeline.executive_summary;
  renderStageDistribution(pipeline.stage_distribution);
  renderBottlenecks(pipeline.bottlenecks);
  renderAging(pipeline.aging_applications);
  renderRoleTable(pipeline.role_wise_status);
  renderPriorityActions(pipeline.priority_actions);
}

function renderEscalationPanel(escalation) {
  $("#escalation-summary").textContent = escalation.summary;

  const queue = $("#escalation-queue");
  if (!escalation.escalation_queue.length) {
    queue.innerHTML = '<p class="empty-state">No escalations — all clear</p>';
  } else {
    queue.innerHTML = escalation.escalation_queue
      .map(
        (e) => `
      <div class="escalation-item ${e.severity}">
        <div class="escalation-header">
          <div>
            <div class="item-title">${e.candidate_name} · ${e.role_title}</div>
            <div class="escalation-id">${e.id} · ${e.category} · ${e.assigned_recruiter}</div>
          </div>
          <div>${severityBadge(e.severity)} ${e.auto_hold ? '<span class="hold-badge">Auto Hold</span>' : ""}</div>
        </div>
        <p style="font-size:0.85rem;margin-bottom:0.35rem">${e.reason}</p>
        <div class="item-action">${e.required_action}</div>
        <div>${(e.policy_refs || []).map((p) => `<span class="policy-tag">${p}</span>`).join("")}</div>
      </div>`
      )
      .join("");
  }

  const fairness = $("#fairness-checks");
  if (!escalation.fairness_checks.length) {
    fairness.innerHTML = '<p class="empty-state">No fairness warnings</p>';
  } else {
    fairness.innerHTML = `<ul class="item-list">${escalation.fairness_checks
      .map(
        (f) => `
      <li>
        <div class="item-title">${f.role_title} — ${f.check_type}</div>
        <div class="item-meta">${f.status}</div>
        <div class="item-action">${f.message}</div>
      </li>`
      )
      .join("")}</ul>`;
  }

  const policies = $("#policy-reminders");
  policies.innerHTML = escalation.policy_reminders
    .map(
      (p) => `
    <li style="opacity:${p.active ? 1 : 0.6}">
      <div class="item-title">${p.id}: ${p.title} ${p.active ? '<span class="badge badge-high">Active</span>' : ""}</div>
      <div class="item-meta">${p.description}</div>
    </li>`
    )
    .join("");

  const audit = $("#audit-recommendations");
  audit.innerHTML = escalation.audit_recommendations.map((r) => `<li>${r}</li>`).join("");
}

async function loadData() {
  const reqFilter = $("#req-filter").value;
  const qs = reqFilter ? `?requisition_id=${encodeURIComponent(reqFilter)}` : "";

  $("#metrics-row").innerHTML = '<div class="loading" style="grid-column:1/-1">Loading agent insights</div>';

  try {
    combinedData = await fetchJSON(`/api/agents/combined${qs}`);
    const { pipeline_insights: pipeline, escalation_compliance: escalation } = combinedData;

    renderMetrics(pipeline, escalation);
    renderPipelinePanel(pipeline);
    renderEscalationPanel(escalation);

    $("#last-updated").textContent = new Date(pipeline.generated_at).toLocaleString();
  } catch (err) {
    console.error(err);
    $("#metrics-row").innerHTML = `<p class="empty-state" style="color:var(--danger)">Failed to load data. Is the server running on port 8000?</p>`;
  }
}

async function init() {
  try {
    requisitions = await fetchJSON("/api/requisitions");
    const select = $("#req-filter");
    requisitions.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r.id;
      opt.textContent = `${r.title} (${r.id})`;
      select.appendChild(opt);
    });
  } catch (e) {
    console.warn("Could not load requisitions", e);
  }

  $$(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      $$(".tab").forEach((t) => t.classList.remove("active"));
      $$(".panel").forEach((p) => p.classList.remove("active"));
      tab.classList.add("active");
      $(`#panel-${tab.dataset.panel}`).classList.add("active");
    });
  });

  $("#req-filter").addEventListener("change", loadData);
  $("#refresh-btn").addEventListener("click", loadData);

  await loadData();
}

document.addEventListener("DOMContentLoaded", init);
