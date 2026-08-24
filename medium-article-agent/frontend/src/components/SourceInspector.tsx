import type { ParseReport } from '../types';
import './SourceInspector.css';

interface Props {
  report?: ParseReport;
}

const TYPE_ORDER = ['heading', 'paragraph', 'list', 'code', 'table', 'slide', 'image', 'quote', 'metadata', 'cell'];

export default function SourceInspector({ report }: Props) {
  if (!report?.files?.length) return null;
  const total = report.total_chars || 0;
  const packed = report.prompt_chars || total;
  const coverage = total ? Math.min(100, Math.round((packed / total) * 100)) : 100;

  return (
    <section className="src-panel">
      <header className="src-head">
        <div>
          <p className="src-kicker">Sources</p>
          <h3>What we kept from the uploads</h3>
        </div>
        <p className="src-meta">
          {report.total_blocks ?? 0} blocks · {total.toLocaleString()} chars
          {report.packed ? ` · packed to ${packed.toLocaleString()} for prompts` : ' · full text fits the prompt'}
        </p>
      </header>
      <div className="src-bar" aria-label={`Source coverage ${coverage}%`}>
        <span style={{ width: `${coverage}%` }} />
      </div>
      <p className="src-bar-lab">
        {report.packed
          ? 'Coverage pack keeps every heading, table, code block, and file. Long paragraphs are sampled last.'
          : 'Every parsed block is sent to the writer. Nothing was truncated.'}
      </p>
      <div className="src-files">
        {report.files.map((file) => (
          <article key={file.filename} className="src-file">
            <header>
              <strong>{file.filename}</strong>
              <span>
                {file.format} · {file.blocks} blocks · {file.chars.toLocaleString()} chars
                {file.pages ? ` · ${file.pages} pages` : ''}
              </span>
            </header>
            <ul className="src-types">
              {TYPE_ORDER.filter((key) => file.by_type?.[key]).map((key) => (
                <li key={key}>
                  <em>{key}</em> {file.by_type?.[key]}
                </li>
              ))}
            </ul>
            {file.warnings?.length ? (
              <p className="src-warn">{file.warnings.join(' · ')}</p>
            ) : null}
          </article>
        ))}
      </div>
      {report.warnings?.length ? (
        <p className="src-warn">{report.warnings.join(' · ')}</p>
      ) : null}
    </section>
  );
}
