import type { LogEntry } from '../types';

export function connectLogStream(
  runId: string,
  onLog: (entry: LogEntry) => void,
  onError?: (err: Event) => void,
): EventSource {
  const es = new EventSource(`/api/stream/${runId}`);
  es.addEventListener('log', (ev) => {
    try {
      const data = JSON.parse(ev.data);
      onLog(data as LogEntry);
    } catch {
      /* ignore parse errors */
    }
  });
  es.onerror = (e) => {
    onError?.(e);
  };
  return es;
}
