/* static/js/voice.js — Voice Debate tab with audio playback */

let voiceTurns = [];
let currentTurnIdx = 0;
let currentAudio = null;
let isPlaying = false;

function initVoiceTab(evalId) {
  const el = document.getElementById('voiceContent');
  el.innerHTML = `
    <div class="card">
      <div class="card-title"><span class="icon">🎙️</span> Voice Debate</div>
      <p class="text-muted" style="font-size:0.88rem; margin-bottom:16px;">
        Listen to the agents debate the candidate with distinct voices via Sarvam AI TTS (Bulbul V3).
        Requires a valid Sarvam API key in your <code>.env</code>.
      </p>
      <button class="btn btn-primary" id="generateVoiceBtn">
        🎙️ Generate Voice Debate
      </button>
      <div id="voiceStatus" style="margin-top:12px;"></div>
    </div>
    <div id="voicePlayer" style="display:none;">
      <div class="voice-controls card">
        <button class="voice-btn" id="prevBtn" title="Previous turn" disabled>⏮</button>
        <button class="voice-btn" id="playBtn" title="Play / Pause">▶</button>
        <button class="voice-btn" id="nextBtn" title="Next turn" disabled>⏭</button>
        <div class="now-playing">
          <div><strong id="npSpeaker">—</strong></div>
          <div id="npText" style="font-size:0.78rem; margin-top:2px;"></div>
        </div>
        <div style="font-size:0.85rem; color:var(--text-muted);" id="turnCounter"></div>
      </div>
      <div id="voiceTurnList"></div>
    </div>
  `;

  document.getElementById('generateVoiceBtn').addEventListener('click', () => generateVoice(evalId));
}

async function generateVoice(evalId) {
  const btn = document.getElementById('generateVoiceBtn');
  const status = document.getElementById('voiceStatus');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generating audio...';
  status.innerHTML = '<div class="text-muted" style="font-size:0.85rem;">Calling Sarvam AI TTS for each debate turn…</div>';

  try {
    const data = await api.post(`/api/voice/${evalId}`);
    voiceTurns = data.turns || [];

    if (voiceTurns.length === 0) {
      status.innerHTML = '<div class="text-muted">No debate turns found.</div>';
      return;
    }

    const withAudio = voiceTurns.filter(t => t.audio_url).length;
    status.innerHTML = withAudio > 0
      ? `<div class="text-muted" style="font-size:0.85rem;">✅ Generated ${withAudio}/${voiceTurns.length} audio clips.</div>`
      : `<div class="text-muted" style="font-size:0.85rem;">⚠️ No audio generated — set SARVAM_API_KEY in .env. Text transcript shown below.</div>`;

    renderVoicePlayer();
    document.getElementById('voicePlayer').style.display = 'block';

  } catch(e) {
    status.innerHTML = `<div class="text-muted" style="color:var(--danger); font-size:0.85rem;">Failed: ${e.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔄 Regenerate';
  }
}

const DEBATE_ICONS = {
  'Technical Agent': '💻', 'HR Agent': '🤝',
  'Hiring Manager Agent': '💼', 'Skeptic Agent': '🔍',
};

function renderVoicePlayer() {
  const list = document.getElementById('voiceTurnList');
  list.innerHTML = voiceTurns.map((t, i) => `
    <div class="debate-turn voice-turn" id="vturn-${i}" style="cursor:pointer;" onclick="jumpToTurn(${i})">
      <div class="debate-avatar ${avatarClass(t.speaker)}">${DEBATE_ICONS[t.speaker] || '🤖'}</div>
      <div class="debate-bubble" style="opacity:${t.audio_url ? 1 : 0.6};">
        <div class="bubble-header">
          <span class="bubble-speaker">${t.speaker}</span>
          <span class="text-muted" style="font-size:0.78rem;">Round ${t.round_number}</span>
          ${t.audio_url
            ? '<span style="color:var(--success); font-size:0.78rem;">🔊 Audio</span>'
            : '<span style="color:var(--text-muted); font-size:0.78rem;">📄 Text only</span>'}
        </div>
        <div class="bubble-message">${t.spoken_text || t.message || ''}</div>
      </div>
    </div>`
  ).join('');

  // Wire up controls
  document.getElementById('playBtn').addEventListener('click', togglePlay);
  document.getElementById('prevBtn').addEventListener('click', () => jumpToTurn(currentTurnIdx - 1));
  document.getElementById('nextBtn').addEventListener('click', () => jumpToTurn(currentTurnIdx + 1));

  jumpToTurn(0);
}

function avatarClass(speaker) {
  const map = {
    'Technical Agent': 'av-technical', 'HR Agent': 'av-hr',
    'Hiring Manager Agent': 'av-hiring', 'Skeptic Agent': 'av-skeptic',
  };
  return map[speaker] || 'av-technical';
}

function jumpToTurn(idx) {
  if (idx < 0 || idx >= voiceTurns.length) return;
  stopAudio();
  currentTurnIdx = idx;

  // Highlight active turn
  document.querySelectorAll('.voice-turn').forEach((el, i) => {
    el.style.outline = i === idx ? '2px solid var(--accent)' : 'none';
    el.style.borderRadius = '8px';
    if (i === idx) el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });

  const turn = voiceTurns[idx];
  document.getElementById('npSpeaker').textContent = turn.speaker;
  document.getElementById('npText').textContent = (turn.spoken_text || '').substring(0, 80) + '...';
  document.getElementById('turnCounter').textContent = `Turn ${idx + 1} / ${voiceTurns.length}`;
  document.getElementById('prevBtn').disabled = idx === 0;
  document.getElementById('nextBtn').disabled = idx === voiceTurns.length - 1;

  if (isPlaying) playCurrentTurn();
}

function togglePlay() {
  if (isPlaying) {
    stopAudio();
    isPlaying = false;
    document.getElementById('playBtn').textContent = '▶';
  } else {
    isPlaying = true;
    document.getElementById('playBtn').textContent = '⏸';
    playCurrentTurn();
  }
}

function stopAudio() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
}

function playCurrentTurn() {
  const turn = voiceTurns[currentTurnIdx];
  if (!turn.audio_url) {
    // No audio — auto-advance after delay proportional to text length
    const delay = Math.max(2000, (turn.spoken_text || '').length * 50);
    setTimeout(() => {
      if (isPlaying) {
        if (currentTurnIdx < voiceTurns.length - 1) jumpToTurn(currentTurnIdx + 1);
        else { isPlaying = false; document.getElementById('playBtn').textContent = '▶'; }
      }
    }, delay);
    return;
  }

  currentAudio = new Audio(turn.audio_url);
  currentAudio.play().catch(() => {});
  currentAudio.onended = () => {
    if (isPlaying) {
      if (currentTurnIdx < voiceTurns.length - 1) jumpToTurn(currentTurnIdx + 1);
      else { isPlaying = false; document.getElementById('playBtn').textContent = '▶'; }
    }
  };
}
