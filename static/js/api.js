/* static/js/api.js — Fetch wrapper */
const api = {
  async _request(method, url, body, isFormData = false) {
    const opts = { method };
    if (body) {
      if (isFormData) {
        opts.body = body;
      } else {
        opts.headers = { 'Content-Type': 'application/json' };
        opts.body = JSON.stringify(body);
      }
    }
    const res = await fetch(url, opts);
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try { const j = await res.json(); detail = j.detail || detail; } catch(e) {}
      const err = new Error(detail);
      err.message = `${res.status}: ${detail}`;
      throw err;
    }
    if (res.status === 204) return null;
    return res.json();
  },
  get: (url) => api._request('GET', url),
  post: (url, body) => api._request('POST', url, body),
  postForm: (url, formData) => api._request('POST', url, formData, true),
};
