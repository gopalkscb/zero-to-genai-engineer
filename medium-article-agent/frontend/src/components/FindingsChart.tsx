import { useState } from 'react';
import type { FindingsPoint } from '../types';
import './FindingsChart.css';

interface Props {
  series?: FindingsPoint[];
}

export default function FindingsChart({ series = [] }: Props) {
  const points = series.filter((p) => p.phase === 'review' || p.phase === 'cap');
  const [picked, setPicked] = useState<number | null>(null);
  const [hover, setHover] = useState<number | null>(null);

  if (points.length < 1) {
    return <p className="fc-empty">Findings chart appears after the first review pass.</p>;
  }

  const width = 640;
  const height = 220;
  const pad = { l: 36, r: 16, t: 16, b: 44 };
  const maxY = Math.max(1, ...points.map((p) => p.open));
  const xs = points.map((_, i) => pad.l + (i * (width - pad.l - pad.r)) / Math.max(points.length - 1, 1));
  const ys = points.map((p) => pad.t + (1 - p.open / maxY) * (height - pad.t - pad.b));
  const line = xs.map((x, i) => `${i === 0 ? 'M' : 'L'} ${x} ${ys[i]}`).join(' ');
  const area = `${line} L ${xs[xs.length - 1]} ${height - pad.b} L ${xs[0]} ${height - pad.b} Z`;
  const active = hover ?? picked;
  const point = active !== null ? points[active] : null;

  const explain = (p: FindingsPoint) => {
    if (p.phase === 'cap') {
      return `Rewrite ${p.iteration} hit the review cap with ${p.open} leftover finding${p.open === 1 ? '' : 's'}. Those were kept as accepted findings instead of being dropped.`;
    }
    if (p.iteration === 0) {
      return `First review of the original draft: ${p.open} finding${p.open === 1 ? '' : 's'} still open (${p.critical} critical, ${p.major} major, ${p.minor} minor). The draft was ${p.word_count} words.`;
    }
    return `After rewrite ${p.iteration}, ${p.open} finding${p.open === 1 ? '' : 's'} were still open (${p.critical} critical, ${p.major} major, ${p.minor} minor). The draft was ${p.word_count} words.`;
  };

  const xLabel = (p: FindingsPoint) => {
    if (p.phase === 'cap') return `Cap ${p.iteration}`;
    if (p.iteration === 0) return '1st review';
    return `After R${p.iteration}`;
  };

  return (
    <div className="fc-wrap">
      <div className="fc-kicker">Open findings by review iteration</div>
      <p className="fc-help">Hover or click a number to read what that pass left open.</p>
      <svg className="fc-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Findings line chart">
        {[0, 0.5, 1].map((t) => {
          const y = pad.t + (1 - t) * (height - pad.t - pad.b);
          return (
            <g key={t}>
              <line x1={pad.l} x2={width - pad.r} y1={y} y2={y} className="fc-grid" />
              <text x={4} y={y + 4} className="fc-axis">
                {Math.round(maxY * t)}
              </text>
            </g>
          );
        })}
        <path d={area} className="fc-area" />
        <path d={line} className="fc-line" />
        {points.map((p, i) => (
          <g key={`${p.iteration}-${p.phase}`}>
            <circle
              cx={xs[i]}
              cy={ys[i]}
              r={active === i ? 7 : 5}
              className={`fc-dot${active === i ? ' is-on' : ''}`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onClick={() => setPicked(i)}
            />
            <text
              x={xs[i]}
              y={height - 10}
              textAnchor="middle"
              className="fc-x"
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onClick={() => setPicked(i)}
            >
              {xLabel(p)}
            </text>
            <text
              x={xs[i]}
              y={ys[i] - 10}
              textAnchor="middle"
              className={`fc-val${active === i ? ' is-on' : ''}`}
              onMouseEnter={() => setHover(i)}
              onMouseLeave={() => setHover(null)}
              onClick={() => setPicked(i)}
            >
              {p.open}
            </text>
          </g>
        ))}
      </svg>
      <p className="fc-readout" aria-live="polite">
        {point ? explain(point) : 'Each point is one review pass. 1st review is the original draft. After R1 is the review that followed the first rewrite.'}
      </p>
    </div>
  );
}
