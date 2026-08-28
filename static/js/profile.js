/* static/js/profile.js — Renders candidate profile tab */

function renderProfile(profile) {
  const el = document.getElementById('profileContent');
  if (!profile || !profile.candidate_name) {
    el.innerHTML = '<div class="empty-state"><div class="icon">👤</div><div>No profile data available</div></div>';
    return;
  }

  const edu = profile.education || {};
  const exp = profile.experience || [];
  const projects = profile.projects || [];
  const claims = profile.candidate_claims || [];

  const skillsHtml = (arr) => arr.length
    ? arr.map(s => `<span class="skill-tag">${s}</span>`).join('')
    : '<span class="text-muted" style="font-size:0.85rem;">None listed</span>';

  const expHtml = exp.map(e => `
    <div class="report-item" style="margin-bottom:12px;">
      <div class="ri-point">${e.role || ''} — <span class="text-muted">${e.company || ''}</span></div>
      <div style="font-size:0.82rem; color:var(--accent2); margin-bottom:6px;">${e.duration || ''} ${e.type ? '· ' + e.type : ''}</div>
      ${e.responsibilities?.length ? `<ul style="padding-left:16px; font-size:0.88rem; color:var(--text-muted);">
        ${e.responsibilities.map(r => `<li>${r}</li>`).join('')}
      </ul>` : ''}
    </div>`).join('') || '<div class="text-muted" style="font-size:0.88rem;">No experience listed</div>';

  const projHtml = projects.map(p => `
    <div class="report-item" style="margin-bottom:12px;">
      <div class="ri-point">${p.name || 'Unnamed Project'}</div>
      <div class="ri-evidence">${p.description || ''}</div>
      ${p.technologies?.length ? `<div class="skill-tags mt-8">${p.technologies.map(t => `<span class="skill-tag">${t}</span>`).join('')}</div>` : ''}
      ${p.outcome ? `<div style="font-size:0.82rem; color:var(--success); margin-top:6px;">📈 ${p.outcome}</div>` : ''}
    </div>`).join('') || '<div class="text-muted" style="font-size:0.88rem;">No projects listed</div>';

  const claimHtml = claims.map(c => {
    const str = c.evidence_strength || 'weak';
    return `<div class="claim-item">
      <div class="claim-text">💬 "${c.claim}"</div>
      <div class="claim-evidence">${c.evidence}</div>
      <div class="claim-strength strength-${str}">Evidence: ${str.toUpperCase()}</div>
    </div>`;
  }).join('') || '<div class="text-muted" style="font-size:0.88rem;">No claims extracted</div>';

  el.innerHTML = `
    <div class="card">
      <div class="card-title"><span class="icon">🎓</span> Education</div>
      <div style="font-size:1rem; font-weight:600;">${edu.degree || 'N/A'}</div>
      <div class="text-muted">${edu.institution || ''}</div>
      <div style="margin-top:6px;">
        ${edu.cgpa ? `<span class="skill-tag">CGPA / Grade: ${edu.cgpa}</span>` : ''}
        ${edu.year_of_graduation ? `<span class="skill-tag">Grad: ${edu.year_of_graduation}</span>` : ''}
      </div>
    </div>

    <div class="card">
      <div class="card-title"><span class="icon">⚡</span> Technical Skills</div>
      <div class="report-section-title">Programming Languages</div>
      <div class="skill-tags">${skillsHtml(profile.programming_languages || [])}</div>
      <div class="report-section-title" style="margin-top:14px;">Frameworks & Libraries</div>
      <div class="skill-tags">${skillsHtml(profile.frameworks || [])}</div>
      <div class="report-section-title" style="margin-top:14px;">Tools & Platforms</div>
      <div class="skill-tags">${skillsHtml([...(profile.tools||[]), ...(profile.platforms||[])])}</div>
      <div class="report-section-title" style="margin-top:14px;">All Skills</div>
      <div class="skill-tags">${skillsHtml(profile.skills || [])}</div>
    </div>

    <div class="card">
      <div class="card-title"><span class="icon">💼</span> Experience</div>
      ${expHtml}
    </div>

    <div class="card">
      <div class="card-title"><span class="icon">🚀</span> Projects</div>
      ${projHtml}
    </div>

    <div class="card">
      <div class="card-title"><span class="icon">💬</span> Candidate Claims & Evidence Strength</div>
      <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:14px;">
        These are key assertions the candidate makes — verified against the documents.
      </div>
      ${claimHtml}
    </div>
  `;
}
