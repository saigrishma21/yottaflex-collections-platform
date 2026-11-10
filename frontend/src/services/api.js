// Robust API client with automatic environment resolution and fallback strategies

function getApiBaseUrl() {
  if (typeof window !== 'undefined') {
    const port = window.location.port;
    // When running under Vite dev server (port 5173) or FastAPI unified server (port 8000)
    if (port === '5173' || port === '8000') {
      return '/api';
    }
    // If accessed via other local dev servers
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return `http://${window.location.hostname}:8000/api`;
    }
  }
  return 'http://127.0.0.1:8000/api';
}

const BASE_URL = getApiBaseUrl();

async function safeFetchJson(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      // If relative URL failed on 5173, fallback to absolute 127.0.0.1:8000
      if (!endpoint.startsWith('http')) {
        const fallbackUrl = `http://127.0.0.1:8000/api${endpoint}`;
        const fallbackRes = await fetch(fallbackUrl, options);
        if (fallbackRes.ok) return fallbackRes.json();
      }
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  } catch (err) {
    // If connection refused, try direct localhost
    if (!endpoint.startsWith('http')) {
      try {
        const fallbackUrl = `http://127.0.0.1:8000/api${endpoint}`;
        const fallbackRes = await fetch(fallbackUrl, options);
        if (fallbackRes.ok) return fallbackRes.json();
      } catch (e) {
        // pass through original error
      }
    }
    throw err;
  }
}

export async function fetchDashboardSummary() {
  return safeFetchJson('/dashboard/summary');
}

export async function fetchDashboardMetrics() {
  return safeFetchJson('/dashboard/metrics');
}

export async function fetchCollections(params = {}) {
  const cleanParams = {};
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '' && v !== 'ALL') {
      cleanParams[k] = v;
    }
  }
  const query = new URLSearchParams(cleanParams).toString();
  const data = await safeFetchJson(`/collections${query ? `?${query}` : ''}`);
  return Array.isArray(data) ? data : (data.cases || data.data || []);
}

export async function fetchPriorityWorklist(limit = 25) {
  try {
    const data = await safeFetchJson(`/collections/priority?limit=${limit}`);
    return Array.isArray(data) ? data : (data.cases || data.data || []);
  } catch (err) {
    console.error('fetchPriorityWorklist failed:', err);
    return [];
  }
}

export async function fetchCaseDetail(caseId) {
  return safeFetchJson(`/collections/${caseId}`);
}

export async function recordContactAttempt(caseId, payload) {
  return safeFetchJson(`/collections/${caseId}/contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function recordPromise(caseId, payload) {
  return safeFetchJson(`/collections/${caseId}/promise`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function fetchPromises(params = {}) {
  const cleanParams = {};
  if (params.status && params.status !== 'ALL') {
    cleanParams.status = params.status;
  }
  const query = new URLSearchParams(cleanParams).toString();
  const data = await safeFetchJson(`/promises${query ? `?${query}` : ''}`);
  return Array.isArray(data) ? data : (data.promises || data.data || []);
}

export async function fetchComplianceIssues() {
  const data = await safeFetchJson('/compliance/issues');
  return Array.isArray(data) ? data : [];
}

export async function fetchComplianceBenchmark() {
  return safeFetchJson('/compliance/benchmark');
}
