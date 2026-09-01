/**
 * API client for the Revenue Leakage Guard backend.
 * Drop this in src/api/client.js in your Vite React frontend.
 *
 * Reads the backend URL from VITE_API_BASE_URL (set in .env.local),
 * falling back to localhost:8000 for local dev.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  // 204 / empty responses
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

// ---- Dashboard aggregates (what your Overview page needs) ----
export const getOverviewKPIs = () => request("/reports/overview");
export const getLeakageTrend = (months = 6) => request(`/reports/trend?months=${months}`);
export const getLeakageByCategory = () => request("/reports/by-category");
export const getTopLeaks = (limit = 10) => request(`/reports/top-leaks?limit=${limit}`);

// ---- Customers ----
export const listCustomers = () => request("/customers");
export const createCustomer = (data) =>
  request("/customers", { method: "POST", body: JSON.stringify(data) });

// ---- Contracts ----
export const listContracts = (customerId) =>
  request(`/contracts${customerId ? `?customer_id=${customerId}` : ""}`);
export const createContract = (data) =>
  request("/contracts", { method: "POST", body: JSON.stringify(data) });
export const extractContractPdf = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BASE_URL}/contracts/extract`, { method: "POST", body: formData });
  if (!res.ok) throw new Error(`Extraction failed: ${res.status}`);
  return res.json();
};

// ---- Entitlements / Usage / Billing ----
export const listEntitlements = (customerId) =>
  request(`/entitlements${customerId ? `?customer_id=${customerId}` : ""}`);
export const createEntitlement = (data) =>
  request("/entitlements", { method: "POST", body: JSON.stringify(data) });

export const listUsage = (customerId) =>
  request(`/usage${customerId ? `?customer_id=${customerId}` : ""}`);
export const recordUsage = (data) =>
  request("/usage", { method: "POST", body: JSON.stringify(data) });

export const listBillingRecords = (customerId) =>
  request(`/billing${customerId ? `?customer_id=${customerId}` : ""}`);
export const createBillingRecord = (data) =>
  request("/billing", { method: "POST", body: JSON.stringify(data) });

// ---- Reconciliation ----
export const runReconciliation = (periodStart, periodEnd) =>
  request(`/reconciliation/run?period_start=${periodStart}&period_end=${periodEnd}`, {
    method: "POST",
  });
export const listReconciliationEvents = (status, customerId) => {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (customerId) params.set("customer_id", customerId);
  const qs = params.toString();
  return request(`/reconciliation${qs ? `?${qs}` : ""}`);
};
export const approveReconciliationEvent = (eventId, approvedBy, resolvedInvoiceId) =>
  request(`/reconciliation/${eventId}/approve`, {
    method: "POST",
    body: JSON.stringify({ approved_by: approvedBy, resolved_invoice_id: resolvedInvoiceId }),
  });
export const rejectReconciliationEvent = (eventId, rejectedBy, reason) =>
  request(`/reconciliation/${eventId}/reject`, {
    method: "POST",
    body: JSON.stringify({ rejected_by: rejectedBy, reason }),
  });

// ---- AI insight ----
export const getLeakInsight = (eventId) => request(`/ai-analysis/insight/${eventId}`);