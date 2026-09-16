const BASE = '/api'

async function jsonOrThrow(response) {
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}))
    throw new Error(detail.detail || 'Request failed.')
  }
  return response.json()
}

export function uploadInvoice(file) {
  const form = new FormData()
  form.append('file', file)
  return fetch(`${BASE}/invoices`, { method: 'POST', body: form }).then(jsonOrThrow)
}

export const listInvoices = () => fetch(`${BASE}/invoices`).then(jsonOrThrow).then(d => d.invoices)
export const getInvoice = (id) => fetch(`${BASE}/invoices/${id}`).then(jsonOrThrow)
export const updateInvoice = (id, fields) =>
  fetch(`${BASE}/invoices/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields)
  }).then(jsonOrThrow)
export const approveInvoice = (id) =>
  fetch(`${BASE}/invoices/${id}/approve`, { method: 'POST' }).then(jsonOrThrow)
export const retryInvoice = (id) =>
  fetch(`${BASE}/invoices/${id}/retry`, { method: 'POST' }).then(jsonOrThrow)
export const getStats = () => fetch(`${BASE}/stats`).then(jsonOrThrow)
export const fileUrl = (id) => `${BASE}/invoices/${id}/file`
export const exportUrl = () => `${BASE}/export.csv`