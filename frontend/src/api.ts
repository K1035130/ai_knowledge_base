const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface ClusterInfo {
  id: number;
  label: string;
  count: number;
  keywords: string[];
}

export interface Highlight {
  month: string;
  text: string;
}

export interface ReportResult {
  overview: {
    total_conversations: number;
    total_messages: number;
    active_days: number;
    avg_session_minutes: number;
    longest_session_minutes: number;
    avg_thread_span_hours: number;
    avg_response_seconds: number;
  };
  activity: {
    by_hour: Record<string, number>;
    by_weekday: Record<string, number>;
    by_month: Record<string, number>;
  };
  language_ratio: Record<string, number>;
  rewrite_rate: {
    total_conversations: number;
    conversations_with_edits: number;
    user_edit_turns: number;
    user_abandoned_versions: number;
    assistant_regen_turns: number;
    assistant_abandoned_versions: number;
    // Verbatim message text. Nothing renders it today, and the static sample report strips it
    // rather than expose real conversation text in a publicly readable file -- so treat it as
    // optional and never assume it is there.
    most_edited?: { conversation_id: string; role: string; edit_count: number; text: string }[];
  };
  clusters: ClusterInfo[];
  monthly_topic_share: Record<string, Record<string, number>>;
  highlights: Highlight[];
}

export interface JobStatus {
  status: "running" | "done" | "error";
  step: string;
  result: ReportResult | null;
  error: string | null;
}

export async function uploadExports(files: File[], lang: "zh" | "en", timezone: string): Promise<string> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  form.append("lang", lang);
  form.append("timezone", timezone);
  const res = await fetch(`${API_BASE}/api/reports`, { method: "POST", body: form });
  if (!res.ok) {
    let detail = `Upload failed: ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // response wasn't JSON — fall back to the generic message
    }
    throw new Error(detail);
  }
  const data = await res.json();
  return data.job_id as string;
}

/**
 * Loads the pre-generated sample report shipped as a static file alongside the frontend.
 *
 * Deliberately not routed through API_BASE: this is served from the same origin as the app
 * (S3/CloudFront), so the sample stays clickable even while the backend EC2 instance is asleep --
 * which is the whole point of having one. BASE_URL keeps it correct under a non-root base path.
 */
export async function fetchDemoReport(lang: "zh" | "en"): Promise<ReportResult> {
  const res = await fetch(`${import.meta.env.BASE_URL}demo-report.${lang}.json`);
  if (!res.ok) {
    throw new Error(`Demo report unavailable: ${res.status}`);
  }
  return (await res.json()) as ReportResult;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/api/reports/${jobId}`);
  if (!res.ok) {
    throw new Error(`Status check failed: ${res.status}`);
  }
  return (await res.json()) as JobStatus;
}
