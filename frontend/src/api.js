const BASE = '/api';
export async function api(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) return res.json();
  return res.text();
}

export async function uploadAudio(file, language = 'hi-IN') {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('language_code', language);
  const res = await fetch(BASE + '/voice/transcribe', { method: 'POST', body: fd });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
