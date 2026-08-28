/* static/js/upload.js — File upload and pipeline trigger */

const resumeFile = document.getElementById('resumeFile');
const transcriptFile = document.getElementById('transcriptFile');
const resumeZone = document.getElementById('resumeZone');
const transcriptZone = document.getElementById('transcriptZone');
const form = document.getElementById('uploadForm');
const submitBtn = document.getElementById('submitBtn');
const submitText = document.getElementById('submitText');
const submitIcon = document.getElementById('submitIcon');
const progressSection = document.getElementById('progressSection');
const statusMsg = document.getElementById('statusMsg');
const progressBar = document.getElementById('progressBar');
const errorSection = document.getElementById('errorSection');
const errorMsg = document.getElementById('errorMsg');

function setupZone(zone, input, nameEl) {
  input.addEventListener('change', () => {
    if (input.files[0]) {
      nameEl.textContent = '✓ ' + input.files[0].name;
      nameEl.style.display = 'block';
      zone.classList.add('has-file');
    }
  });
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event('change'));
    }
  });
}

setupZone(resumeZone, resumeFile, document.getElementById('resumeName'));
setupZone(transcriptZone, transcriptFile, document.getElementById('transcriptName'));

function setProgress(pct, msg) {
  progressBar.style.width = pct + '%';
  statusMsg.textContent = msg;
}

function showError(msg) {
  errorSection.style.display = 'block';
  errorMsg.textContent = msg;
  submitBtn.disabled = false;
  submitText.textContent = 'Start Evaluation';
  submitIcon.textContent = '🚀';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  if (!resumeFile.files[0]) {
    alert('Please upload a resume file.');
    return;
  }

  // Reset error
  errorSection.style.display = 'none';

  // Lock button
  submitBtn.disabled = true;
  submitIcon.innerHTML = '<span class="spinner"></span>';
  submitText.textContent = 'Uploading...';
  progressSection.style.display = 'block';
  setProgress(10, 'Uploading files to server...');

  const formData = new FormData();
  formData.append('resume', resumeFile.files[0]);
  if (transcriptFile.files[0]) {
    formData.append('transcript', transcriptFile.files[0]);
  }
  formData.append('target_role', document.getElementById('targetRole').value || 'Software Engineer');

  try {
    setProgress(30, 'Extracting text from documents...');
    const uploadResult = await api.postForm('/api/upload', formData);

    setProgress(60, 'Files processed. Redirecting to evaluation...');
    const evalId = uploadResult.evaluation_id;

    setProgress(90, 'Starting evaluation pipeline...');
    await new Promise(r => setTimeout(r, 500));

    setProgress(100, 'Redirecting...');
    window.location.href = `/results.html?id=${evalId}`;

  } catch (err) {
    showError(err.message || 'Upload failed. Please try again.');
  }
});
