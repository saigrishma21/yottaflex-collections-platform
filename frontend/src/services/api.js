const BASE_URL = 'http://127.0.0.1:8000/api';

export async function fetchDashboardSummary() {
  const res = await fetch(`${BASE_URL}/dashboard/summary`);
  if (!res.ok) throw new Error('Failed to fetch dashboard summary');
  return res.json();
}

export async function fetchDashboardMetrics() {
  const res = await fetch(`${BASE_URL}/dashboard/metrics`);
  if (!res.ok) throw new Error('Failed to fetch dashboard metrics');
  return res.json();
}

export async function fetchCollections(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE_URL}/collections?${query}`);
  if (!res.ok) throw new Error('Failed to fetch collection cases');
  return res.json();
}

export async function fetchPriorityWorklist(limit = 25) {
  const res = await fetch(`${BASE_URL}/collections/priority?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch priority worklist');
  return res.json();
}

export async function fetchCaseDetail(caseId) {
  const res = await fetch(`${BASE_URL}/collections/${caseId}`);
  if (!res.ok) throw new Error(`Failed to fetch case ${caseId}`);
  return res.json();
}

export async function recordContactAttempt(caseId, payload) {
  const res = await fetch(`${BASE_URL}/collections/${caseId}/contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to record contact');
  }
  return res.json();
}

export async function recordPromise(caseId, payload) {
  const res = await fetch(`${BASE_URL}/collections/${caseId}/promise`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to record promise');
  }
  return res.json();
}

export async function fetchPromises(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE_URL}/promises?${query}`);
  if (!res.ok) throw new Error('Failed to fetch promises');
  return res.json();
}

export async function fetchComplianceIssues() {
  const res = await fetch(`${BASE_URL}/compliance/issues`);
  if (!res.ok) throw new Error('Failed to fetch compliance issues');
  return res.json();
}

export async function fetchComplianceBenchmark() {
  const res = await fetch(`${BASE_URL}/compliance/benchmark`);
  if (!res.ok) throw new Error('Failed to fetch compliance benchmark');
  return res.json();
}
