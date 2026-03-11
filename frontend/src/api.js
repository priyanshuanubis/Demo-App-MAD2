const API_BASE = 'http://localhost:5000/api';

export async function apiRequest(path, { token = '', method = 'GET', body = null } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  const contentType = res.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await res.json() : await res.text();
  if (!res.ok) {
    throw new Error(payload.message || 'Request failed');
  }
  return payload;
}
