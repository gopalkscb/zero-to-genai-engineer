import type { ConfigStatus, ExportArtifacts, IterationSnapshot, JobRecord, RunStatus } from '../types';

const BASE = '';

export async function getRecentRuns(): Promise<{ runs: JobRecord[] }> {
  const res = await fetch(`${BASE}/api/pipeline/recent`);
  if (!res.ok) throw new Error('Failed to load recent runs');
  return res.json();
}

export async function getConfig(): Promise<ConfigStatus> {
  const res = await fetch(`${BASE}/api/pipeline/config`);
  if (!res.ok) throw new Error('Failed to load config');
  return res.json();
}

export async function startPipeline(
  files: File[],
  topicHint: string,
  enableWebResearch = false,
): Promise<{ run_id: string; status: string }> {
  const form = new FormData();
  form.append('topic_hint', topicHint);
  form.append('enable_web_research', enableWebResearch ? 'true' : 'false');
  files.forEach((f) => form.append('files', f));
  const res = await fetch(`${BASE}/api/pipeline/start`, { method: 'POST', body: form });
  if (!res.ok) throw new Error('Failed to start pipeline');
  return res.json();
}

export async function getIteration(
  runId: string,
  iteration: number,
  phase?: string,
): Promise<IterationSnapshot> {
  const query = phase ? `?phase=${encodeURIComponent(phase)}` : '';
  const res = await fetch(`${BASE}/api/pipeline/${runId}/iterations/${iteration}${query}`);
  if (!res.ok) throw new Error('Iteration not found');
  return res.json();
}

export async function getRunStatus(runId: string): Promise<RunStatus> {
  const res = await fetch(`${BASE}/api/pipeline/${runId}/status`);
  if (!res.ok) throw new Error('Failed to get status');
  return res.json();
}

export async function resumeRun(runId: string): Promise<{
  run_id: string;
  status: string;
  resumed: boolean;
  next_nodes?: string[];
  detail?: string;
}> {
  const res = await fetch(`${BASE}/api/pipeline/${runId}/resume`, { method: 'POST' });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || 'Failed to resume pipeline');
  }
  return res.json();
}

export async function approveRun(
  runId: string,
  approved: boolean,
  changeNotes = '',
): Promise<{ run_id: string; status: string }> {
  const res = await fetch(`${BASE}/api/pipeline/${runId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved, change_notes: changeNotes }),
  });
  if (!res.ok) throw new Error('Failed to submit approval');
  return res.json();
}

export async function getExport(runId: string): Promise<{ run_id: string; export: ExportArtifacts }> {
  const res = await fetch(`${BASE}/api/export/${runId}`);
  if (!res.ok) throw new Error('Export not ready');
  return res.json();
}

export async function copyToClipboard(runId: string): Promise<string> {
  const res = await fetch(`${BASE}/api/export/${runId}/clipboard`);
  if (!res.ok) throw new Error('Clipboard not ready');
  const data = await res.json();
  await navigator.clipboard.writeText(data.clipboard_text);
  return data.clipboard_text;
}
