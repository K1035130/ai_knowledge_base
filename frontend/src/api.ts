const API_BASE = "http://localhost:8000";

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
    most_edited: { conversation_id: string; role: string; edit_count: number; text: string }[];
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

export async function uploadExports(files: File[], lang: "zh" | "en"): Promise<string> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  form.append("lang", lang);
  const res = await fetch(`${API_BASE}/api/reports`, { method: "POST", body: form });
  if (!res.ok) {
    throw new Error(`Upload failed: ${res.status}`);
  }
  const data = await res.json();
  return data.job_id as string;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/api/reports/${jobId}`);
  if (!res.ok) {
    throw new Error(`Status check failed: ${res.status}`);
  }
  return (await res.json()) as JobStatus;
}
