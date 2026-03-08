/**
 * FSMGuard API Client
 * Connects the frontend to the FastAPI backend at localhost:8000
 */

const BASE_URL = "http://localhost:8000";

// ─────────────────────────────────────────
// Types (mirror what FastAPI returns)
// ─────────────────────────────────────────

export interface JobStatusResponse {
  job_id: string;
  status: "uploaded" | "pending" | "running" | "completed" | "failed";
  progress: number;
  message?: string;
  created_at: number;
  updated_at: number;
}

export interface BackendVulnerability {
  id: string;
  state: string;
  cwe: string;
  risk_score: number;
  fix_category: string;
  fix_parameter: string;
  fix_strictness: string;
}

export interface AnalysisResultsResponse {
  job_id: string;
  status: string;
  filename: string;
  vulnerabilities_found: number;
  vulnerabilities_fixed: number;
  design_safe: boolean;
  vulnerability_list?: BackendVulnerability[];
  stages: Record<string, unknown>;
  files: {
    patched?: string;
    report?: string;
  };
}

// ─────────────────────────────────────────
// Upload
// ─────────────────────────────────────────

export async function uploadVerilogText(
  code: string,
  filename = "design.v"
): Promise<{ job_id: string; filename: string; size: number }> {
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

export async function startAnalysis(jobId: string): Promise<void> {
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

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${BASE_URL}/api/status/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}

export async function getResults(jobId: string): Promise<AnalysisResultsResponse> {
  const res = await fetch(`${BASE_URL}/api/results/${jobId}`);
  if (!res.ok) throw new Error("Failed to fetch results");
  return res.json();
}

// ─────────────────────────────────────────
// Download helpers
// ─────────────────────────────────────────

export function getPatchedFileUrl(jobId: string): string {
  return `${BASE_URL}/api/download/patched/${jobId}`;
}

export function getReportUrl(jobId: string, format: "json" | "txt" = "txt"): string {
  return `${BASE_URL}/api/download/report/${jobId}?format=${format}`;
}

export async function fetchPatchedCode(jobId: string): Promise<string> {
  const res = await fetch(getPatchedFileUrl(jobId));
  if (!res.ok) throw new Error("Patched file not available yet");
  return res.text();
}

// ─────────────────────────────────────────
// Poll until job reaches terminal state
// ─────────────────────────────────────────

export async function pollUntilDone(
  jobId: string,
  onProgress: (status: JobStatusResponse) => void,
  intervalMs = 1500
): Promise<JobStatusResponse> {
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId);
        onProgress(status);

        if (status.status === "completed" || status.status === "failed") {
          clearInterval(timer);
          resolve(status);
        }
      } catch (e) {
        clearInterval(timer);
        reject(e);
      }
    }, intervalMs);
  });
}
