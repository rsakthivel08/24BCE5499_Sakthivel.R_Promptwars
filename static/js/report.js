/* static/js/report.js — Renders the Final Report tab */

const REC_COLORS = {
  'Strong Hire':          ['#2dce89', '#1aab6d'],
  'Hire':                 ['#6c63ff', '#5a52dd'],
  'Proceed to Interview': ['#00d4aa', '#00b892'],
  'Hold':                 ['#f5a623', '#d4891a'],
  'Reject':               ['#ff4f6a', '#dd3a53'],
};

function renderReport(report) {
  const el = document.getElementById('reportContent');
  if (!report || !report.final_recommendation) {
    el.innerHTML = '<div class="empty-state"><div class="icon">⚖️</div><div>Final report not available</div></div>';
    return;
  }

  const rec = report.final_recommendation || 'Unknown';
  const colors = REC_COLORS[rec] || ['#6c63ff', '#5a52dd'];
  const conf = Math.round((report.confidence_score || 0) * 100);

  // Agent score summary table
  const scores = report.agent_score_summary || {};
  const scoreRows = Object.entries(scores).map(([name, s]) =>
    `<tr>
       <td>${name}</td>
       <td><strong>${s.score || '–'}</strong>/10</td>
       <td>${s.assessment || ''}</td>
       <td>${Math.round((s.confidence || 0) * 100)}%</td>
     </tr>`
  ).join('');

  // Strengths
  const strengthsHtml = (report.key_strengths || []).map(s => `
    <div class="report-item">
      <div class="ri-point">✓ ${s.point}</div>
      <div class="ri-evidence">"${s.evidence}"</div>
    </div>`).join('') || '<div class="text-muted" style="font-size:0.88rem;">None recorded</div>';

  // Concerns
  const concernsHtml = (report.key_concerns || []).map(c => `
    <div class="report-item">
      <div class="ri-point">⚠️ ${c.point}</div>
      <div class="ri-evidence">"${c.evidence}"</div>
      <span class="sev sev-${c.severity || 'medium'}">${c.severity || 'medium'}</span>
    </div>`).join('') || '<div class="text-muted" style="font-size:0.88rem;">None recorded</div>';

  // Unresolved disagreements
  const unresHtml = (report.unresolved_disagreements || []).map(d => {
    const posHtml = Object.entries(d.agent_positions || {}).map(([a, pos]) =>
      `<div class="agent-pos"><span class="aname">${a}:</span> ${pos}</div>`
    ).join('');
    return `<div class="unresolved-item">
      <div class="unresolved-topic">🔴 ${d.topic}</div>
      ${posHtml}
      <div style="margin-top:8px; font-size:0.8rem; color:var(--text-muted);">Status: ${d.status}</div>
    </div>`;
  }).join('') || '<div class="report-item"><div class="text-muted" style="font-size:0.88rem;">✅ No major unresolved disagreements</div></div>';

  // Interview questions
  const qHtml = (report.suggested_interview_questions || []).map((q, i) =>
    `<div class="interview-q"><span class="q-num">Q${i+1}.</span><span>${q}</span></div>`
  ).join('') || '<div class="text-muted" style="font-size:0.88rem;">None suggested</div>';

  el.innerHTML = `
    <!-- Recommendation Banner -->
    <div class="recommendation-banner" style="background: linear-gradient(135deg, ${colors[0]} 0%, ${colors[1]} 100%);">
      <div class="rec-label">Final Recommendation</div>
      <div class="rec-value">${rec}</div>
      <div class="rec-confidence">Confidence: ${report.confidence_level || ''} (${conf}%)</div>
    </div>

    <!-- Reasoning -->
    <div class="card">
      <div class="card-title"><span class="icon">🧠</span> Judge's Reasoning</div>
      <div class="reasoning-box">${report.reasoning || 'No reasoning provided.'}</div>

      <div class="report-section-title">Agent Score Summary (NOT averaged)</div>
      <table class="agent-score-table">
        <thead><tr><th>Agent</th><th>Score</th><th>Assessment</th><th>Confidence</th></tr></thead>
        <tbody>${scoreRows}</tbody>
      </table>
      <div style="font-size:0.78rem; color:var(--text-muted); margin-top:8px;">
        ⚠️ These scores were NOT averaged. The judge weighed evidence strength, severity, and agent disagreements.
      </div>
    </div>

    <!-- Strengths & Concerns -->
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
      <div class="card" style="margin:0;">
        <div class="card-title"><span class="icon">💪</span> Key Strengths</div>
        ${strengthsHtml}
      </div>
      <div class="card" style="margin:0;">
        <div class="card-title"><span class="icon">⚠️</span> Key Concerns</div>
        ${concernsHtml}
      </div>
    </div>

    <!-- Unresolved Disagreements -->
    <div class="card" style="margin-top:20px;">
      <div class="card-title"><span class="icon">🔴</span> Unresolved Agent Disagreements</div>
      <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:14px;">
        These are points the agents debated but could not fully resolve.
      </div>
      ${unresHtml}
    </div>

    <!-- Interview Questions -->
    <div class="card">
      <div class="card-title"><span class="icon">❓</span> Suggested Interview Questions</div>
      ${qHtml}
    </div>
  `;
}
