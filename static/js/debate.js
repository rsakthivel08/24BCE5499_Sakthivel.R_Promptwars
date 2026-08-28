/* static/js/debate.js — Renders the Agent Debate tab */

const DEBATE_AVATAR = {
  'Technical Agent':      { cls: 'av-technical', icon: '💻' },
  'HR Agent':             { cls: 'av-hr',        icon: '🤝' },
  'Hiring Manager Agent': { cls: 'av-hiring',    icon: '💼' },
  'Skeptic Agent':        { cls: 'av-skeptic',   icon: '🔍' },
};

function stanceLabel(stance) {
  const map = {
    agree:            'Agrees',
    disagree:         'Disagrees',
    partially_agree:  'Partially Agrees',
    challenge:        'Challenges',
    update_opinion:   'Updates Opinion',
    new_concern:      'New Concern',
  };
  return map[stance] || stance;
}

function renderTurn(turn) {
  const meta = DEBATE_AVATAR[turn.speaker] || { cls: 'av-technical', icon: '🤖' };
  const stance = turn.stance || 'challenge';
  const addressing = turn.addressing && turn.addressing !== turn.speaker
    ? `→ <em>${turn.addressing}</em>` : '';

  return `
  <div class="debate-turn" data-speaker="${turn.speaker}" data-round="${turn.round_number}">
    <div class="debate-avatar ${meta.cls}">${meta.icon}</div>
    <div class="debate-bubble">
      <div class="bubble-header">
        <span class="bubble-speaker">${turn.speaker}</span>
        ${addressing ? `<span class="bubble-addressing">${addressing}</span>` : ''}
        <span class="stance-badge stance-${stance}">${stanceLabel(stance)}</span>
        ${turn.opinion_change && turn.opinion_change !== 'none'
          ? `<span class="stance-badge stance-update_opinion">Opinion Updated</span>` : ''}
      </div>
      <div class="bubble-message">${turn.message || ''}</div>
      ${turn.evidence_cited || turn.evidence
        ? `<div class="bubble-evidence">📎 "${turn.evidence_cited || turn.evidence}"</div>` : ''}
      ${turn.point_being_discussed
        ? `<div style="font-size:0.78rem; color:var(--text-muted); margin-top:6px;">
             Topic: <em>${turn.point_being_discussed}</em>
           </div>` : ''}
    </div>
  </div>`;
}

function renderDebate(turns) {
  const el = document.getElementById('debateContent');
  if (!turns || turns.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="icon">⚔️</div><div>No debate transcript available</div></div>';
    return;
  }

  // Group turns by round_number
  const rounds = {};
  turns.forEach(t => {
    const r = t.round_number || 1;
    if (!rounds[r]) rounds[r] = [];
    rounds[r].push(t);
  });

  const roundNames = { 1: '🗡️ Round 1 — Challenge Phase', 2: '🛡️ Round 2 — Response Phase' };

  let html = `
    <div style="margin-bottom:16px; font-size:0.88rem; color:var(--text-muted);">
      ⚔️ Agents now see each other's evaluations and respond directly. This is a real debate — agents can agree, disagree, and revise their opinions.
    </div>`;

  Object.keys(rounds).sort().forEach(rn => {
    html += `<div class="debate-round-title">${roundNames[rn] || 'Round ' + rn}</div>`;
    html += rounds[rn].map(renderTurn).join('');
  });

  el.innerHTML = html;
}
