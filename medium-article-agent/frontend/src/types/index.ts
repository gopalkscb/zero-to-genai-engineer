/** Section 5 contracts mirrored for frontend */

export type PipelineStatus =
  | 'pending'
  | 'running'
  | 'paused_hitl'
  | 'completed'
  | 'failed';

export interface LogEntry {
  timestamp: string;
  node: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  message: string;
  iteration?: number;
  trace_url?: string;
}

export interface Finding {
  finding_id: string;
  reviewer: string;
  severity: 'critical' | 'major' | 'minor';
  problem: string;
  suggested_fix: string;
  resolved?: boolean;
}

export interface SkillsCheck {
  id: string;
  label: string;
  passed: boolean;
  severity?: string;
  detail?: string;
  suggested_fix?: string;
}

export interface SkillsAudit {
  word_count?: number;
  title?: string;
  banned_hits?: string[];
  passed?: number;
  failed?: number;
  checks?: SkillsCheck[];
}

export interface ParseFileReport {
  filename: string;
  format: string;
  chars: number;
  blocks: number;
  pages?: number;
  by_type?: Record<string, number>;
  warnings?: string[];
}

export interface ParseReport {
  files?: ParseFileReport[];
  total_chars?: number;
  total_blocks?: number;
  by_type?: Record<string, number>;
  warnings?: string[];
  packed?: boolean;
  prompt_chars?: number;
}

export interface ImageAsset {
  image_id: string;
  prompt: string;
  url: string;
  caption: string;
  status: 'pending' | 'generated' | 'skipped_error' | 'skipped_limit';
  review_passed?: boolean;
  review_notes?: string;
}

export interface ExportArtifacts {
  markdown: string;
  html: string;
  clipboard_text: string;
  export_path: string;
}

export interface IterationSnapshot {
  iteration: number;
  phase: string;
  summary: string;
  markdown?: string;
  excerpt: string;
  word_count: number;
  char_count: number;
  open_findings_count: number;
  findings: Finding[];
  findings_by_reviewer: Record<string, number>;
  findings_by_severity: Record<string, number>;
  timestamp: string;
}

export interface NodeEvent {
  node: string;
  message: string;
  iteration: number;
  timestamp: string;
  level: string;
}

export interface FindingsPoint {
  iteration: number;
  phase: string;
  open: number;
  critical: number;
  major: number;
  minor: number;
  word_count: number;
}

export type GraphPhaseId = 'prepare' | 'review' | 'finish';
export type GraphEdgeKind = 'always' | 'fanout' | 'loop' | 'exit' | 'hitl';

export interface GraphNodeSpec {
  id: string;
  label: string;
  row: number;
  col: number;
  phase?: GraphPhaseId | string;
  does?: string;
  visit_means?: string;
}

export interface GraphEdgeSpec {
  from: string;
  to: string;
  kind?: GraphEdgeKind | string;
  label?: string;
  when?: string;
}

export interface GraphPhaseSpec {
  id: string;
  label: string;
  rows: number[];
  blurb: string;
}

export interface GraphSpec {
  nodes: GraphNodeSpec[];
  edges: GraphEdgeSpec[];
  phases?: GraphPhaseSpec[];
}

export interface JobRecord {
  run_id: string;
  status: string;
  topic_hint: string;
  title?: string;
  iteration?: number;
  open_findings_count?: number;
  updated_at?: string;
  preview_url?: string;
  pipeline_url?: string;
}

export interface RunStatus {
  run_id: string;
  status: PipelineStatus;
  iteration: number;
  open_findings_count: number;
  blocking_findings_count?: number;
  resolved_findings_count?: number;
  converged: boolean;
  cap_hit_with_open_findings: boolean;
  stalled?: boolean;
  logs: LogEntry[];
  error?: string;
  final_markdown?: string;
  images?: ImageAsset[];
  title?: string;
  max_iterations?: number;
  last_node?: string;
  progress_hint?: string;
  preview_url?: string;
  pipeline_url?: string;
  node_visits?: Record<string, number>;
  findings_series?: FindingsPoint[];
  iterations?: IterationSnapshot[];
  open_findings?: Finding[];
  accepted_findings?: Finding[];
  resolved_findings?: Finding[];
  graph?: GraphSpec;
  node_events?: NodeEvent[];
  editor_score?: number;
  editor_notes?: string;
  parse_report?: ParseReport;
  skills_audit?: SkillsAudit;
  subtitle?: string;
  tags?: string[];
}

export interface ConfigStatus {
  style_guide: { loaded: boolean; path: string; chars: number };
  llm_provider: string;
  image_count: number;
  max_review_iterations?: number;
}
