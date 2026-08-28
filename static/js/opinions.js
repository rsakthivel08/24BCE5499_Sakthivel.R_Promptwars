/* static/js/opinions.js — Renders Agent Opinions tab */

const AGENT_META = {
  'Technical Agent':       { cls: 'technical', icon: '💻', color: '#6c63ff' },
  'HR Agent':              { cls: 'hr',        icon: '🤝', color: '#00d4aa' },
  'Hiring Manager Agent':  { cls: 'hiring',    icon: '💼', color: '#f5a623' },
  'Skeptic Agent':         { cls: 'skeptic',   icon: '🔍', color: '#ff4f6a' },
};

function scoreClass(score) {
  if (score >= 7) return 'score-high';
  if (score >= 5) return 'score-mid';
  return 'score-low';
}

function renderEvidencedList(items, type) {
  if (!items || items.length === 0) return `<div class="text-muted" style="font-size:0.85rem;">None noted</div>`;
  return `<ul class="evidenced-list">${items.map(item => `
    <li>
      <div class="point">${type === 'concern' ? '⚠️ ' : '✓ '}${item.point || ''}</div>
      <div class="evidence">"${item.evidence || ''}"</div>
      ${type === 'concern' && item.severity ? `<span class="sev sev-${item.severity}">${item.severity}</span>` : ''}
    </li>`).join('')}</ul>`;
}

function renderOpinions(opinions) {
  const el = document.getElementById('opinionsContent');
  if (!opinions || opinions.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="icon">🤖</div><div>No agent opinions available</div></div>';
    return;
  }

  const cardsHtml = opinions.map(op => {
    const meta = AGENT_META[op.agent] || { cls: 'technical', icon: '🤖', color: '#6c63ff' };
    const sc = op.score || 0;
    const conf = Math.round((op.confidence || 0) * 100);

    return `
    <div class="agent-card ${meta.cls}">
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <span style="font-size:1.5rem;">${meta.icon}</span>
        <div>
          <div class="agent-name">${op.agent}</div>
          <div class="agent-assessment">${op.overall_assessment || ''}</div>
        </div>
      </div>

      <div class="score-row">
        <div class="score-circle ${scoreClass(sc)}">${sc}</div>
        <div class="confidence-bar">
          <div class="confidence-label">Confidence: ${conf}%</div>
          <div class="conf-track"><div class="conf-fill" style="width:${conf}%"></div></div>
        </div>
      </div>

      <div style="font-size:0.88rem; color:var(--text-muted); margin-bottom:14px; font-style:italic;">
        ${op.summary || ''}
      </div>

      <details style="margin-bottom:12px;">
        <summary style="cursor:pointer; font-weight:600; font-size:0.88rem; color:var(--success); margin-bottom:8px;">
          ✓ Strengths (${(op.strengths||[]).length})
        </summary>
        ${renderEvidencedList(op.strengths, 'strength')}
      </details>

      <details style="margin-bottom:12px;">
        <summary style="cursor:pointer; font-weight:600; font-size:0.88rem; color:var(--danger); margin-bottom:8px;">
          ⚠ Concerns (${(op.concerns||[]).length})
        </summary>
        ${renderEvidencedList(op.concerns, 'concern')}
      </details>

      <div style="background:var(--surface); border-radius:8px; padding:10px 12px; font-size:0.88rem;">
        <span style="color:var(--text-muted); font-weight:600;">Recommendation: </span>${op.recommendation || ''}
      </div>

      ${(op.questions_for_interview||[]).length ? `
      <details style="margin-top:12px;">
        <summary style="cursor:pointer; font-weight:600; font-size:0.85rem; color:var(--text-muted);">
          ❓ Interview Questions (${op.questions_for_interview.length})
        </summary>
        <ol style="padding-left:18px; margin-top:8px; font-size:0.85rem; color:var(--text-muted);">
          ${op.questions_for_interview.map(q => `<li style="margin-bottom:4px;">${q}</li>`).join('')}
        </ol>
      </details>` : ''}
    </div>`;
  }).join('');

  el.innerHTML = `
    <div style="margin-bottom:16px; font-size:0.88rem; color:var(--text-muted);">
      ℹ️ Each agent evaluated the candidate <strong>independently</strong> — no agent saw another's opinion before this point.
    </div>
    <div class="agents-grid">${cardsHtml}</div>`;
}
