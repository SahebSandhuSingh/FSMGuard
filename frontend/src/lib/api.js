/**
 * FSMGuard API Client
 * Connects the frontend to the FastAPI backend at localhost:8000
 */
const BASE_URL = "http://localhost:8000";
// ─────────────────────────────────────────
// Upload
// ─────────────────────────────────────────
export async function uploadVerilogText(code, filename = "design.v") {
    const blob = new Blob([code], { type: "text/plain" });
    const file = new File([blob], filename, { type: "text/plain" });
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/api/upload`, {
        method: "POST",
        body: formData,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(err.detail ?? "Upload failed");
    }
    return res.json();
}
// ─────────────────────────────────────────
// Analyze
// ─────────────────────────────────────────
export async function startAnalysis(jobId) {
    const res = await fetch(`${BASE_URL}/api/analyze/${jobId}`, {
        method: "POST",
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Failed to start analysis" }));
        throw new Error(err.detail ?? "Failed to start analysis");
    }
}
// ─────────────────────────────────────────
// Status polling
// ─────────────────────────────────────────
export async function getJobStatus(jobId) {
    const res = await fetch(`${BASE_URL}/api/status/${jobId}`);
    if (!res.ok)
        throw new Error("Failed to fetch status");
    return res.json();
}
export async function getResults(jobId) {
    const res = await fetch(`${BASE_URL}/api/results/${jobId}`);
    if (!res.ok)
        throw new Error("Failed to fetch results");
    return res.json();
}
// ─────────────────────────────────────────
// Download helpers
// ─────────────────────────────────────────
export function getPatchedFileUrl(jobId) {
    return `${BASE_URL}/api/download/patched/${jobId}`;
}
export function getReportUrl(jobId, format = "txt") {
    return `${BASE_URL}/api/download/report/${jobId}?format=${format}`;
}
export async function getFsmGraph(jobId) {
    const res = await fetch(`${BASE_URL}/api/fsm/${jobId}`);
    if (!res.ok)
        throw new Error("Failed to fetch FSM graph");
    return res.json();
}
export function getOriginalFileUrl(jobId) {
    return `${BASE_URL}/api/download/original/${jobId}`;
}
export async function fetchOriginalCode(jobId) {
    const res = await fetch(getOriginalFileUrl(jobId));
    if (!res.ok)
        throw new Error("Original file not found");
    return res.text();
}
export async function fetchPatchedCode(jobId) {
    const res = await fetch(getPatchedFileUrl(jobId));
    if (!res.ok)
        throw new Error("Patched file not available yet");
    return res.text();
}
// ─────────────────────────────────────────
// Poll until job reaches terminal state
// ─────────────────────────────────────────
export async function pollUntilDone(jobId, onProgress, intervalMs = 1500) {
    return new Promise((resolve, reject) => {
        const timer = setInterval(async () => {
            try {
                const status = await getJobStatus(jobId);
                onProgress(status);
                if (status.status === "completed" || status.status === "failed") {
                    clearInterval(timer);
                    resolve(status);
                }
            }
            catch (e) {
                clearInterval(timer);
                reject(e);
            }
        }, intervalMs);
    });
}
