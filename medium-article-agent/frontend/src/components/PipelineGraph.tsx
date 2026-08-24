import { useMemo, useState, type FocusEvent, type MouseEvent } from 'react';
import type { GraphEdgeSpec, GraphSpec, NodeEvent, PipelineStatus } from '../types';
import { mergeGraph, nodeLabel } from './pipelineCatalog';
import './PipelineGraph.css';

interface Props {
  graph?: GraphSpec;
  visits?: Record<string, number>;
  lastNode?: string;
  iteration?: number;
  maxIterations?: number;
  openFindings?: number;
  converged?: boolean;
  capHit?: boolean;
  status?: PipelineStatus | string;
  events?: NodeEvent[];
}

type Selection =
  | { kind: 'node'; id: string }
  | { kind: 'metric'; id: string }
  | { kind: 'edge'; from: string; to: string }
  | { kind: 'phase'; id: string };

type Tip = { x: number; y: number; title: string; body: string };
type Pt = { x: number; y: number };

const LAYOUT: Record<string, { c: number; r: number }> = {
  ingest: { c: 0, r: 0 },
  plan: { c: 1, r: 0 },
  web_research: { c: 2, r: 0 },
  draft: { c: 3, r: 0 },
  image_gen: { c: 4, r: 0 },
  image_review: { c: 4, r: 1 },
  image_redraw: { c: 5.2, r: 1 },
  reviewer_technical: { c: 0, r: 2 },
  reviewer_style: { c: 1, r: 2 },
  reviewer_structure: { c: 2, r: 2 },
  reviewer_grounding: { c: 3, r: 2 },
  reviewer_reader: { c: 4, r: 2 },
  reviewer_skills: { c: 5.2, r: 2 },
  supervisor: { c: 0.3, r: 3 },
  rewrite: { c: 1.7, r: 3 },
  rewrite_voice: { c: 3.1, r: 3 },
  editor_score: { c: 4.55, r: 3 },
  headline: { c: 0, r: 4 },
  style_pass: { c: 1, r: 4 },
  final_rewrite: { c: 2, r: 4 },
  grounding_recheck: { c: 3, r: 4 },
  human_gate: { c: 4.2, r: 4 },
  export: { c: 5.4, r: 4 },
};

const COL = 148;
const ROW = 108;
const NW = 122;
const NH = 40;
const PAD_X = 28;
const PAD_Y = 34;
const REVIEWERS = [
  'reviewer_technical',
  'reviewer_style',
  'reviewer_structure',
  'reviewer_grounding',
  'reviewer_reader',
  'reviewer_skills',
];
const maxC = Math.max(...Object.values(LAYOUT).map((slot) => slot.c));
const maxR = Math.max(...Object.values(LAYOUT).map((slot) => slot.r));

function boxOf(id: string) {
  const slot = LAYOUT[id] || { c: 0, r: 0 };
  const x = PAD_X + slot.c * COL;
  const y = PAD_Y + slot.r * ROW;
  return {
    id,
    x,
    y,
    w: NW,
    h: NH,
    cx: x + NW / 2,
    cy: y + NH / 2,
    l: x,
    r: x + NW,
    t: y,
    b: y + NH,
  };
}

function poly(points: Pt[]): string {
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
}

function kindLabel(kind?: string): string {
  if (kind === 'fanout') return 'Fan-out';
  if (kind === 'loop') return 'Loop';
  if (kind === 'exit') return 'Exit';
  if (kind === 'hitl') return 'Return';
  return 'Next';
}

export default function PipelineGraph({
  graph,
  visits = {},
  lastNode,
  iteration = 0,
  maxIterations = 10,
  openFindings = 0,
  converged = false,
  capHit = false,
  status,
  events = [],
}: Props) {
  const { nodes, edges, phases } = useMemo(() => mergeGraph(graph), [graph]);
  const [selected, setSelected] = useState<Selection | null>({ kind: 'metric', id: 'loops' });
  const [tip, setTip] = useState<Tip | null>(null);

  const width = PAD_X * 2 + maxC * COL + NW;
  const height = PAD_Y * 2 + maxR * ROW + NH + 8;
  const boxes = useMemo(() => Object.fromEntries(nodes.map((node) => [node.id, boxOf(node.id)])), [nodes]);

  const rewriteRuns = visits.rewrite || 0;
  const reviewLoops = Math.max(rewriteRuns, iteration);
  const supervisorRuns = visits.supervisor || 0;
  const reviewerPasses = Math.max(0, ...REVIEWERS.map((id) => visits[id] || 0));
  const nodesFired = nodes.filter((node) => (visits[node.id] || 0) > 0).length;

  const metrics = [
    {
      id: 'loops',
      value: reviewLoops,
      label: 'Review loops',
      title: `${reviewLoops} review loops`,
      body:
        reviewLoops === 0
          ? 'No rewrite has run yet. Loop 0 is the first review of the original draft.'
          : `Rewrite ran ${reviewLoops} time${reviewLoops === 1 ? '' : 's'}. Each loop sends still-open findings back into the draft.`,
    },
    {
      id: 'iteration',
      value: `${iteration}/${maxIterations}`,
      label: 'Iteration cap',
      title: `Iteration ${iteration} of ${maxIterations}`,
      body: capHit
        ? 'The cap was hit. Leftover findings were kept as accepted findings.'
        : converged && openFindings === 0
          ? 'The loop exited because no findings remain open.'
          : `${Math.max(0, maxIterations - iteration)} rewrite${maxIterations - iteration === 1 ? '' : 's'} left before leftover findings are accepted.`,
    },
    {
      id: 'findings',
      value: openFindings,
      label: 'Open findings',
      title: `${openFindings} open findings`,
      body:
        openFindings === 0
          ? 'Nothing is still open. The supervisor can exit to the editor score gate.'
          : 'These stay open until the assigned reviewer marks the same ID resolved.',
    },
    {
      id: 'supervisor',
      value: supervisorRuns,
      label: 'Supervisor scores',
      title: `Supervisor scored ${supervisorRuns} time${supervisorRuns === 1 ? '' : 's'}`,
      body: 'One merge of the six reviewers per pass. Usually one higher than review loops.',
    },
    {
      id: 'reviewers',
      value: reviewerPasses,
      label: 'Reviewer passes',
      title: `${reviewerPasses} specialist passes`,
      body: 'Highest specialist count. Each of the six reviewers runs once per loop.',
    },
    {
      id: 'visited',
      value: `${nodesFired}/${nodes.length}`,
      label: 'Nodes visited',
      title: `${nodesFired} of ${nodes.length} nodes have run`,
      body: 'A visit is one execution. Prepare nodes stay at 1. Review-loop nodes climb.',
    },
  ];

  const showTip = (event: MouseEvent<HTMLElement> | FocusEvent<HTMLElement>, title: string, body: string) => {
    const host = event.currentTarget.closest('.lg-wrap') as HTMLElement | null;
    const box = host?.getBoundingClientRect();
    const rect = event.currentTarget.getBoundingClientRect();
    if (!box) return;
    setTip({
      x: Math.min(rect.left - box.left + rect.width / 2, box.width - 190),
      y: rect.bottom - box.top + 8,
      title,
      body,
    });
  };

  const visitCopy = (id: string, label: string, meaning: string, count: number) =>
    count === 0
      ? { title: `${label} has not run`, body: meaning }
      : { title: `${label} ran ${count} time${count === 1 ? '' : 's'}`, body: meaning };

  const incoming = (id: string) => edges.filter((edge) => edge.to === id);
  const outgoing = (id: string) => edges.filter((edge) => edge.from === id);
  const selectedNode = selected?.kind === 'node' ? nodes.find((node) => node.id === selected.id) : undefined;
  const selectedMetric = selected?.kind === 'metric' ? metrics.find((item) => item.id === selected.id) : undefined;
  const selectedEdge =
    selected?.kind === 'edge' ? edges.find((edge) => edge.from === selected.from && edge.to === selected.to) : undefined;
  const selectedPhase = selected?.kind === 'phase' ? phases.find((phase) => phase.id === selected.id) : undefined;

  const related = new Set<string>();
  if (selected?.kind === 'node') {
    related.add(selected.id);
    incoming(selected.id).forEach((edge) => related.add(edge.from));
    outgoing(selected.id).forEach((edge) => related.add(edge.to));
  }

  const edgeOn = (edge: GraphEdgeSpec) => {
    if (selected?.kind === 'edge') return selected.from === edge.from && selected.to === edge.to;
    if (selected?.kind === 'node') return edge.from === selected.id || edge.to === selected.id;
    return false;
  };

  const routes = useMemo(() => buildRoutes(boxes), [boxes]);
  const recent = selectedNode
    ? events.filter((event) => event.node === selectedNode.id).slice(-4).reverse()
    : [];

  return (
    <div className="lg-wrap">
      <header className="lg-head">
        <div>
          <p className="lg-kicker">LangGraph</p>
          <h2 className="lg-title">Editorial pipeline</h2>
        </div>
        <p className={`lg-status is-${status || 'pending'}`}>
          {status === 'paused_hitl'
            ? 'Paused for review'
            : status === 'completed'
              ? 'Complete'
              : status === 'running'
                ? 'Running'
                : status === 'failed'
                  ? 'Failed'
                  : 'Idle'}
          {lastNode ? ` · ${nodeLabel(lastNode)}` : ''}
        </p>
      </header>

      <div className="lg-metrics" role="list">
        {metrics.map((metric) => (
          <button
            key={metric.id}
            type="button"
            role="listitem"
            className={`lg-metric${selected?.kind === 'metric' && selected.id === metric.id ? ' is-on' : ''}`}
            onMouseEnter={(event) => showTip(event, metric.title, metric.body)}
            onMouseLeave={() => setTip(null)}
            onFocus={(event) => showTip(event, metric.title, metric.body)}
            onBlur={() => setTip(null)}
            onClick={() => setSelected({ kind: 'metric', id: metric.id })}
            aria-label={`${metric.value} ${metric.label}. ${metric.body}`}
          >
            <span className="lg-metric-num">{metric.value}</span>
            <span className="lg-metric-lab">{metric.label}</span>
          </button>
        ))}
      </div>

      <div className="lg-stage">
        <div className="lg-board">
          <svg className="lg-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="LangGraph pipeline">
            <defs>
              <marker id="lg-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
                <path d="M 0 1.2 L 9 5 L 0 8.8 Z" fill="#7a756c" />
              </marker>
            </defs>
            {phases.map((phase) => {
              const rows = phase.rows;
              const top = PAD_Y + Math.min(...rows) * ROW - 30;
              const bandH = rows.length * ROW - 30;
              return (
                <g key={phase.id}>
                  <rect x={12} y={top} width={width - 24} height={bandH} rx={10} className={`lg-band is-${phase.id}`} />
                  <text x={20} y={top + 16} className="lg-band-label">
                    {phase.label}
                  </text>
                </g>
              );
            })}
            {routes.map((route, routeIndex) => {
              const active = edgeOn(route.edge);
              const dim = selected && !active && (selected.kind === 'node' || selected.kind === 'edge');
              return (
                <g key={`${route.edge.from}-${route.edge.to}-${routeIndex}`}>
                  <path
                    d={route.d}
                    className={`lg-edge is-${route.edge.kind || 'always'}${active ? ' is-on' : ''}${dim ? ' is-dim' : ''}`}
                    markerEnd="url(#lg-arrow)"
                  />
                  <path
                    d={route.d}
                    className="lg-edge-hit"
                    onClick={() => setSelected({ kind: 'edge', from: route.edge.from, to: route.edge.to })}
                    onMouseEnter={(event) => {
                      const host = event.currentTarget.ownerSVGElement?.closest('.lg-wrap') as HTMLElement | null;
                      const hostBox = host?.getBoundingClientRect();
                      if (!hostBox) return;
                      setTip({
                        x: event.clientX - hostBox.left,
                        y: event.clientY - hostBox.top + 12,
                        title: `${nodeLabel(route.edge.from)} → ${nodeLabel(route.edge.to)}`,
                        body: route.edge.when || kindLabel(route.edge.kind),
                      });
                    }}
                    onMouseLeave={() => setTip(null)}
                  />
                  {route.label && (
                    <text x={route.label.x} y={route.label.y} textAnchor="middle" className="lg-edge-label">
                      {route.label.text}
                    </text>
                  )}
                </g>
              );
            })}
            {nodes.map((node) => {
              const box = boxes[node.id];
              const count = visits[node.id] || 0;
              const active = lastNode === node.id;
              const on = selected?.kind === 'node' && selected.id === node.id;
              const dim = selected?.kind === 'node' && !related.has(node.id);
              const copy = visitCopy(node.id, node.label, node.visit_means || '', count);
              return (
                <g
                  key={node.id}
                  className={`lg-node${count ? ' is-done' : ''}${active ? ' is-active' : ''}${on ? ' is-on' : ''}${dim ? ' is-dim' : ''}`}
                  transform={`translate(${box.x}, ${box.y})`}
                  onClick={() => setSelected({ kind: 'node', id: node.id })}
                  onMouseEnter={(event) => {
                    const host = event.currentTarget.ownerSVGElement?.closest('.lg-wrap') as HTMLElement | null;
                    const hostBox = host?.getBoundingClientRect();
                    if (!hostBox) return;
                    setTip({
                      x: event.clientX - hostBox.left,
                      y: event.clientY - hostBox.top + 14,
                      title: node.label,
                      body: `${node.does || ''} ${copy.title}.`,
                    });
                  }}
                  onMouseLeave={() => setTip(null)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') setSelected({ kind: 'node', id: node.id });
                  }}
                >
                  <title>{`${node.label}. ${copy.title}. ${node.does}`}</title>
                  <rect width={NW} height={NH} rx={8} />
                  <text x={NW / 2} y={20} textAnchor="middle" className="lg-node-name">
                    {node.label}
                  </text>
                  <text x={NW / 2} y={34} textAnchor="middle" className="lg-node-phase">
                    {node.phase}
                  </text>
                  {count > 0 && (
                    <g
                      transform={`translate(${NW - 2}, 2)`}
                      onClick={(event) => {
                        event.stopPropagation();
                        setSelected({ kind: 'node', id: node.id });
                      }}
                    >
                      <circle r={10} className="lg-slug" />
                      <text y={3} textAnchor="middle" className="lg-slug-text">
                        {count}
                      </text>
                    </g>
                  )}
                </g>
              );
            })}
          </svg>
        </div>

        <aside className="lg-inspect" aria-live="polite">
          {selectedNode && (
            <>
              <p className="lg-inspect-kicker">{selectedNode.phase} node</p>
              <h3>{selectedNode.label}</h3>
              <p>{selectedNode.does}</p>
              <div className="lg-inspect-num">
                <strong>{visits[selectedNode.id] || 0}</strong>
                <span>{visitCopy(selectedNode.id, selectedNode.label, selectedNode.visit_means || '', visits[selectedNode.id] || 0).body}</span>
              </div>
              <div className="lg-wires">
                <div>
                  <h4>Arrives from</h4>
                  {incoming(selectedNode.id).length ? (
                    incoming(selectedNode.id).map((edge) => (
                      <button
                        key={`${edge.from}-${edge.to}`}
                        type="button"
                        onClick={() => setSelected({ kind: 'edge', from: edge.from, to: edge.to })}
                      >
                        {nodeLabel(edge.from)}
                        <em>{edge.label || kindLabel(edge.kind)}</em>
                      </button>
                    ))
                  ) : (
                    <p>Graph start</p>
                  )}
                </div>
                <div>
                  <h4>Leaves toward</h4>
                  {outgoing(selectedNode.id).length ? (
                    outgoing(selectedNode.id).map((edge) => (
                      <button
                        key={`${edge.from}-${edge.to}`}
                        type="button"
                        onClick={() => setSelected({ kind: 'edge', from: edge.from, to: edge.to })}
                      >
                        {nodeLabel(edge.to)}
                        <em>{edge.label || kindLabel(edge.kind)}</em>
                      </button>
                    ))
                  ) : (
                    <p>Graph end</p>
                  )}
                </div>
              </div>
              {recent.length > 0 && (
                <ul className="lg-events">
                  {recent.map((event, idx) => (
                    <li key={`${event.timestamp}-${idx}`}>
                      <time>{event.timestamp?.slice(11, 19)}</time>
                      {event.message}
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
          {selectedMetric && (
            <>
              <p className="lg-inspect-kicker">What this number is</p>
              <h3>{selectedMetric.title}</h3>
              <p>{selectedMetric.body}</p>
            </>
          )}
          {selectedEdge && (
            <>
              <p className="lg-inspect-kicker">{kindLabel(selectedEdge.kind)} connection</p>
              <h3>
                {nodeLabel(selectedEdge.from)} → {nodeLabel(selectedEdge.to)}
              </h3>
              <p>{selectedEdge.when}</p>
            </>
          )}
          {selectedPhase && (
            <>
              <p className="lg-inspect-kicker">Lane</p>
              <h3>{selectedPhase.label}</h3>
              <p>{selectedPhase.blurb}</p>
            </>
          )}
          {!selected && (
            <>
              <p className="lg-inspect-kicker">Read the graph</p>
              <h3>Select a node or number</h3>
              <p>Hover for a short note. Click to pin what the step does and how it is wired.</p>
            </>
          )}
        </aside>
      </div>

      <div className="lg-legend">
        {phases.map((phase) => (
          <button
            key={phase.id}
            type="button"
            className={`lg-chip${selected?.kind === 'phase' && selected.id === phase.id ? ' is-on' : ''}`}
            onClick={() => setSelected({ kind: 'phase', id: phase.id })}
          >
            {phase.label}
          </button>
        ))}
        <span className="lg-key is-always">Next step</span>
        <span className="lg-key is-loop">Loop</span>
        <span className="lg-key is-exit">Exit</span>
        <span className="lg-key is-hitl">Human return</span>
      </div>

      {tip && (
        <div className="lg-tip" style={{ left: tip.x, top: tip.y }} role="tooltip">
          <strong>{tip.title}</strong>
          <span>{tip.body}</span>
        </div>
      )}
    </div>
  );
}

function buildRoutes(boxes: Record<string, ReturnType<typeof boxOf>>): {
  edge: GraphEdgeSpec;
  d: string;
  label?: { x: number; y: number; text: string };
}[] {
  const routes: { edge: GraphEdgeSpec; d: string; label?: { x: number; y: number; text: string } }[] = [];
  const add = (edge: GraphEdgeSpec, points: Pt[], label?: { x: number; y: number; text: string }) => {
    routes.push({ edge, d: poly(points), label });
  };

  const chain = [
    ['ingest', 'plan', 'sources ready'],
    ['plan', 'web_research', 'outline ready'],
    ['web_research', 'draft', 'write draft'],
    ['draft', 'image_gen', 'illustrate'],
  ] as const;
  for (const [from, to, label] of chain) {
    const a = boxes[from];
    const b = boxes[to];
    if (!a || !b) continue;
    add({ from, to, kind: 'always', label, when: 'Always.' }, [
      { x: a.r, y: a.cy },
      { x: b.l, y: b.cy },
    ]);
  }

  const images = boxes.image_gen;
  const art = boxes.image_review;
  const redraw = boxes.image_redraw;
  if (images && art) {
    add(
      { from: 'image_gen', to: 'image_review', kind: 'always', label: 'art direction', when: 'Every generated figure is vision-checked.' },
      [
        { x: images.cx, y: images.b },
        { x: art.cx, y: art.t },
      ],
    );
  }
  if (art && redraw) {
    add(
      { from: 'image_review', to: 'image_redraw', kind: 'loop', label: 'rejected', when: 'Failed figures regenerate, up to two redraws.' },
      [
        { x: art.r, y: art.cy },
        { x: redraw.l, y: redraw.cy },
      ],
      { x: (art.r + redraw.l) / 2, y: art.cy - 8, text: 'redraw' },
    );
    add(
      { from: 'image_redraw', to: 'image_review', kind: 'loop', label: 're-check', when: 'New bytes go back to art-direction.' },
      [
        { x: redraw.cx, y: redraw.b },
        { x: redraw.cx, y: redraw.b + 10 },
        { x: art.cx, y: art.b + 10 },
        { x: art.cx, y: art.b },
      ],
    );
  }

  const reviewerBoxes = REVIEWERS.map((id) => boxes[id]).filter(Boolean);
  const fanSource = art || images;
  if (fanSource && reviewerBoxes.length) {
    const busY = (fanSource.b + reviewerBoxes[0].t) / 2;
    add(
      {
        from: 'image_review',
        to: 'reviewer_technical',
        kind: 'fanout',
        label: 'fan out',
        when: 'After figures pass or the redraw cap is hit, all six reviewers run in parallel.',
      },
      [
        { x: fanSource.cx, y: fanSource.b },
        { x: fanSource.cx, y: busY },
        { x: reviewerBoxes[0].cx, y: busY },
      ],
    );
    for (const node of reviewerBoxes) {
      add(
        { from: 'image_review', to: node.id, kind: 'fanout', label: 'fan out', when: 'Parallel specialist review.' },
        [
          { x: node.cx, y: busY },
          { x: node.cx, y: node.t },
        ],
      );
    }
  }

  const supervisor = boxes.supervisor;
  if (supervisor && reviewerBoxes.length) {
    const joinY = (reviewerBoxes[0].b + supervisor.t) / 2;
    for (const node of reviewerBoxes) {
      add(
        { from: node.id, to: 'supervisor', kind: 'always', label: 'findings', when: 'Each reviewer sends its verdict to the supervisor.' },
        [
          { x: node.cx, y: node.b },
          { x: node.cx, y: joinY },
          { x: supervisor.cx, y: joinY },
          { x: supervisor.cx, y: supervisor.t },
        ],
      );
    }
  }

  const rewrite = boxes.rewrite;
  const voice = boxes.rewrite_voice;
  const editor = boxes.editor_score;
  if (supervisor && rewrite) {
    add(
      { from: 'supervisor', to: 'rewrite', kind: 'loop', label: 'findings remain', when: 'If any finding is still open and the cap has not been hit.' },
      [
        { x: supervisor.r, y: supervisor.cy },
        { x: rewrite.l, y: rewrite.cy },
      ],
      { x: (supervisor.r + rewrite.l) / 2, y: supervisor.cy - 8, text: 'findings remain' },
    );
  }
  if (rewrite && voice) {
    add(
      { from: 'rewrite', to: 'rewrite_voice', kind: 'always', label: 'polish voice', when: 'Always after a substance rewrite.' },
      [
        { x: rewrite.r, y: rewrite.cy },
        { x: voice.l, y: voice.cy },
      ],
    );
  }

  if (voice && reviewerBoxes.length) {
    const loopY = reviewerBoxes[0].b + 8;
    add(
      { from: 'rewrite_voice', to: 'reviewer_technical', kind: 'loop', label: 're-review', when: 'After voice polish, reviewers verdict the same finding IDs.' },
      [
        { x: voice.cx, y: voice.t },
        { x: voice.cx, y: loopY },
        { x: reviewerBoxes[0].cx, y: loopY },
      ],
      { x: voice.cx, y: loopY + 14, text: 're-review' },
    );
    for (const node of reviewerBoxes) {
      add(
        { from: 'rewrite_voice', to: node.id, kind: 'loop', label: 're-review', when: 'Re-check previous findings.' },
        [
          { x: node.cx, y: loopY },
          { x: node.cx, y: node.b },
        ],
      );
    }
  }

  if (supervisor && editor) {
    add(
      { from: 'supervisor', to: 'editor_score', kind: 'exit', label: 'clean or cap', when: 'If findings are closed, or the loop stalled, or the iteration cap was hit.' },
      [
        { x: supervisor.cx, y: supervisor.b },
        { x: supervisor.cx, y: supervisor.b + 14 },
        { x: editor.cx, y: supervisor.b + 14 },
        { x: editor.cx, y: editor.t },
      ],
      { x: (supervisor.cx + editor.cx) / 2, y: supervisor.b + 8, text: 'editor gate' },
    );
  }
  if (editor && rewrite) {
    add(
      { from: 'editor_score', to: 'rewrite', kind: 'loop', label: 'below bar', when: 'If the editor score is under 8 and retries remain.' },
      [
        { x: editor.cx, y: editor.b },
        { x: editor.cx, y: editor.b + 12 },
        { x: rewrite.cx, y: editor.b + 12 },
        { x: rewrite.cx, y: rewrite.b },
      ],
    );
  }

  const headline = boxes.headline;
  if (editor && headline) {
    add(
      { from: 'editor_score', to: 'headline', kind: 'exit', label: 'publication bar', when: 'If the score is at least 8, or the editor retry cap was hit.' },
      [
        { x: editor.cx, y: editor.b },
        { x: editor.cx, y: (editor.b + headline.t) / 2 },
        { x: headline.cx, y: (editor.b + headline.t) / 2 },
        { x: headline.cx, y: headline.t },
      ],
    );
  }

  const finish = [
    ['headline', 'style_pass'],
    ['style_pass', 'final_rewrite'],
    ['final_rewrite', 'grounding_recheck'],
    ['grounding_recheck', 'human_gate'],
    ['human_gate', 'export'],
  ] as const;
  for (const [from, to] of finish) {
    const a = boxes[from];
    const b = boxes[to];
    if (!a || !b) continue;
    add(
      {
        from,
        to,
        kind: from === 'human_gate' ? 'exit' : 'always',
        label: to === 'export' ? 'approved' : '',
        when: 'Always along the finish lane, unless a loop fires.',
      },
      [
        { x: a.r, y: a.cy },
        { x: b.l, y: b.cy },
      ],
    );
  }

  const ground = boxes.grounding_recheck;
  const final = boxes.final_rewrite;
  if (ground && final) {
    const lift = ground.t - 14;
    add(
      { from: 'grounding_recheck', to: 'final_rewrite', kind: 'loop', label: 'still drifting', when: 'If grounding finds drift and it has retried fewer than twice.' },
      [
        { x: ground.cx, y: ground.t },
        { x: ground.cx, y: lift },
        { x: final.cx, y: lift },
        { x: final.cx, y: final.t },
      ],
    );
  }

  const human = boxes.human_gate;
  if (human && rewrite) {
    const gutter = human.r + 18;
    const under = human.b + 16;
    add(
      { from: 'human_gate', to: 'rewrite', kind: 'hitl', label: 'changes requested', when: 'If you send the draft back with notes.' },
      [
        { x: human.cx, y: human.b },
        { x: human.cx, y: under },
        { x: gutter, y: under },
        { x: gutter, y: rewrite.cy },
        { x: rewrite.r, y: rewrite.cy },
      ],
      { x: gutter - 4, y: (under + rewrite.cy) / 2, text: 'changes' },
    );
  }

  return routes;
}
