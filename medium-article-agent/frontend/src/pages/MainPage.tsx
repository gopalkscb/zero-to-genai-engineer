import { useCallback, useEffect, useState } from 'react';
import {
  Button,
  ContentLayout,
  Header,
  SpaceBetween,
  Tabs,
  Textarea,
} from '@cloudscape-design/components';
import { approveRun, copyToClipboard, getExport, getRecentRuns, getRunStatus, resumeRun } from '../api/client';
import { connectLogStream } from '../api/sse';
import ArticlePreview from '../components/ArticlePreview';
import FindingsChart from '../components/FindingsChart';
import FindingsPanel from '../components/FindingsPanel';
import ImageReviewPanel from '../components/ImageReviewPanel';
import IterationStudio from '../components/IterationStudio';
import IterationTracker from '../components/IterationTracker';
import JobsBoard from '../components/JobsBoard';
import LogFeed from '../components/LogFeed';
import MonitoringDashboard from '../components/MonitoringDashboard';
import PipelineGraph from '../components/PipelineGraph';
import SkillsChecklist from '../components/SkillsChecklist';
import SourceInspector from '../components/SourceInspector';
import UploadPanel from '../components/UploadPanel';
import type { ImageAsset, JobRecord, LogEntry, RunStatus } from '../types';
import './MainPage.css';

function logKey(entry: LogEntry): string {
  return `${entry.timestamp}|${entry.node}|${entry.message}`;
}

function mergeLogs(prev: LogEntry[], incoming: LogEntry[]): LogEntry[] {
  const seen = new Set(prev.map(logKey));
  const next = [...prev];
  for (const entry of incoming) {
    const key = logKey(entry);
    if (!seen.has(key)) {
      seen.add(key);
      next.push(entry);
    }
  }
  return next;
}

function readParam(name: string): string | null {
  return new URLSearchParams(window.location.search).get(name);
}

function writeUrl(id: string | null, view?: string, mode: 'push' | 'replace' = 'push') {
  const url = new URL(window.location.href);
  if (id) url.searchParams.set('run', id);
  else url.searchParams.delete('run');
  if (view && view !== 'story') url.searchParams.set('view', view);
  else url.searchParams.delete('view');
  const next = `${url.pathname}${url.search}`;
  if (mode === 'push') window.history.pushState({ run: id, view }, '', next);
  else window.history.replaceState({ run: id, view }, '', next);
}

export default function MainPage() {
  const [runId, setRunId] = useState<string | null>(() => readParam('run'));
  const [view, setView] = useState(() => readParam('view') || 'story');
  const [status, setStatus] = useState<RunStatus | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [markdown, setMarkdown] = useState('');
  const [images, setImages] = useState<ImageAsset[]>([]);
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [changeNotes, setChangeNotes] = useState('');
  const [message, setMessage] = useState('');
  const [resuming, setResuming] = useState(false);

  const refreshJobs = useCallback(() => {
    getRecentRuns()
      .then((data) => setJobs(data.runs || []))
      .catch(() => {});
  }, []);

  const openJob = (id: string, nextView: 'story' | 'pipeline' = 'story') => {
    setLogs([]);
    setStatus(null);
    setMarkdown('');
    setImages([]);
    setMessage('');
    setRunId(id);
    setView(nextView);
    writeUrl(id, nextView);
  };

  const handleStarted = (id: string) => openJob(id, 'pipeline');

  const handleNewArticle = () => {
    setRunId(null);
    setStatus(null);
    setLogs([]);
    setMarkdown('');
    setImages([]);
    setMessage('');
    setView('story');
    writeUrl(null);
    refreshJobs();
  };

  const refreshStatus = useCallback(async (id: string) => {
    try {
      const s = await getRunStatus(id);
      setStatus(s);
      if (s.logs?.length) {
        setLogs((prev) => mergeLogs(prev, s.logs));
      }
      if (s.final_markdown) {
        setMarkdown(s.final_markdown);
      }
      if (s.images?.length) {
        setImages(s.images);
      }
    } catch {
      /* polling */
    }
  }, []);

  useEffect(() => {
    refreshJobs();
  }, [refreshJobs]);

  useEffect(() => {
    const onPop = () => {
      const id = readParam('run');
      setRunId(id);
      setView(readParam('view') || 'story');
      if (!id) {
        setStatus(null);
        setLogs([]);
        setMarkdown('');
        setImages([]);
        refreshJobs();
      }
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [refreshJobs]);

  useEffect(() => {
    if (!runId) return;
    const es = connectLogStream(runId, (entry) => setLogs((prev) => mergeLogs(prev, [entry])));
    const running = status?.status === 'running';
    const interval = setInterval(() => refreshStatus(runId), running ? 2000 : 5000);
    refreshStatus(runId);
    return () => {
      es.close();
      clearInterval(interval);
    };
  }, [runId, refreshStatus, status?.status]);

  const handleResume = async () => {
    if (!runId) return;
    setResuming(true);
    try {
      const result = await resumeRun(runId);
      setMessage(result.detail || 'Resumed LangGraph from the last checkpoint.');
      await refreshStatus(runId);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Could not resume');
    } finally {
      setResuming(false);
    }
  };

  const handleApprove = async (approved: boolean) => {
    if (!runId) return;
    await approveRun(runId, approved, changeNotes);
    setMessage(approved ? 'Approved — exporting...' : 'Changes requested — rewriting...');
    if (approved) {
      const exp = await getExport(runId);
      setMarkdown(exp.export.markdown);
    }
    refreshStatus(runId);
  };

  const handleExport = async () => {
    if (!runId) return;
    await copyToClipboard(runId);
    setMessage('Copied to clipboard! Paste into Medium editor.');
  };

  const changeView = (next: string) => {
    setView(next);
    writeUrl(runId, next, 'replace');
  };

  return (
        <div className="maa-shell">
          <div className="maa-toolbar">
            <Header
              variant="h1"
              actions={
                runId ? (
                  <Button onClick={handleNewArticle}>Back to jobs</Button>
                ) : undefined
              }
            >
              Medium Article Agent
            </Header>
          </div>
          {!runId && (
            <div className="maa-home">
              <UploadPanel onStarted={handleStarted} />
              <div className="maa-home-jobs">
                <JobsBoard jobs={jobs} onOpen={openJob} />
              </div>
            </div>
          )}
          {runId && (
          <ContentLayout>
              <div className={`maa-tabs${view === 'pipeline' ? ' is-pipeline' : ''}`}>
                <SpaceBetween size="l">
                  <MonitoringDashboard
                    status={status}
                    onResume={handleResume}
                    resuming={resuming}
                  />
                  <IterationTracker
                    iteration={status?.iteration ?? 0}
                    maxIterations={status?.max_iterations ?? 10}
                  />
                  <Tabs
                    activeTabId={view}
                    onChange={({ detail }) => changeView(detail.activeTabId)}
                    tabs={[
                      {
                        id: 'story',
                        label: 'Story',
                        content: (
                          <SpaceBetween size="l">
                            <ArticlePreview
                              markdown={markdown}
                              images={images}
                              subtitle={status?.subtitle}
                              tags={status?.tags}
                            />
                            <ImageReviewPanel images={images} />
                            <SkillsChecklist audit={status?.skills_audit} />
                            <SourceInspector report={status?.parse_report} />
                          </SpaceBetween>
                        ),
                      },
                      {
                        id: 'pipeline',
                        label: 'Pipeline demo',
                        content: (
                          <SpaceBetween size="l">
                            <PipelineGraph
                              graph={status?.graph}
                              visits={status?.node_visits}
                              lastNode={status?.last_node}
                              iteration={status?.iteration ?? 0}
                              maxIterations={status?.max_iterations ?? 10}
                              openFindings={status?.open_findings_count ?? 0}
                              converged={status?.converged}
                              capHit={status?.cap_hit_with_open_findings}
                              status={status?.status}
                              events={
                                status?.node_events?.length
                                  ? status.node_events
                                  : logs.map((entry) => ({
                                      node: entry.node,
                                      message: entry.message,
                                      iteration: entry.iteration ?? 0,
                                      timestamp: entry.timestamp,
                                      level: entry.level,
                                    }))
                              }
                            />
                            <FindingsChart series={status?.findings_series} />
                            <IterationStudio
                              runId={runId}
                              iterations={status?.iterations}
                              liveMarkdown={markdown}
                              images={images}
                              accepted={status?.accepted_findings}
                            />
                            {status?.cap_hit_with_open_findings ? (
                              <FindingsPanel
                                findings={status?.accepted_findings || []}
                                title="Leftover findings accepted at the cap"
                                description="The loop hit its iteration cap, so these were accepted rather than dropped."
                              />
                            ) : (
                              <FindingsPanel
                                findings={status?.open_findings || []}
                                description="Still open. Each stays until its reviewer marks the same ID resolved."
                              />
                            )}
                            <LogFeed logs={logs} />
                          </SpaceBetween>
                        ),
                      },
                      {
                        id: 'review',
                        label: 'Review & export',
                        content: (
                          <SpaceBetween size="m">
                            <SkillsChecklist audit={status?.skills_audit} />
                            {status?.status === 'paused_hitl' ? (
                              <SpaceBetween direction="horizontal" size="s">
                                <Button variant="primary" onClick={() => handleApprove(true)}>
                                  Approve & Export
                                </Button>
                                <Textarea
                                  value={changeNotes}
                                  onChange={({ detail }) => setChangeNotes(detail.value)}
                                  placeholder="Change notes (optional)"
                                />
                                <Button onClick={() => handleApprove(false)}>Request Changes</Button>
                              </SpaceBetween>
                            ) : null}
                            {status?.status === 'completed' ? (
                              <Button variant="primary" onClick={handleExport}>
                                Copy to Clipboard
                              </Button>
                            ) : null}
                            {message ? <p>{message}</p> : null}
                          </SpaceBetween>
                        ),
                      },
                    ]}
                  />
                </SpaceBetween>
              </div>
          </ContentLayout>
          )}
        </div>
  );
}
