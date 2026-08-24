import { useEffect, useState } from 'react';
import { Badge, Button, Container, Header, SpaceBetween } from '@cloudscape-design/components';
import { getIteration } from '../api/client';
import type { Finding, ImageAsset, IterationSnapshot } from '../types';
import ArticlePreview from './ArticlePreview';
import FindingsPanel from './FindingsPanel';
import './IterationStudio.css';

interface Props {
  runId: string;
  iterations?: IterationSnapshot[];
  liveMarkdown: string;
  images?: ImageAsset[];
  accepted?: Finding[];
}

function passLabel(item: IterationSnapshot): string {
  if (item.phase === 'draft') return 'First draft';
  if (item.phase === 'review' && item.iteration === 0) return 'First review';
  if (item.phase === 'review') return `Review after rewrite ${item.iteration}`;
  if (item.phase === 'rewrite') return `Rewrite ${item.iteration}`;
  if (item.phase === 'voice') return `Voice polish ${item.iteration}`;
  if (item.phase === 'editor') return `Editor score ${item.iteration}`;
  if (item.phase === 'headline') return 'Headline';
  if (item.phase === 'style') return 'Style polish';
  if (item.phase === 'final') return 'Final polish';
  if (item.phase === 'cap') return `Stopped at cap (${item.iteration})`;
  return item.phase;
}

export default function IterationStudio({
  runId,
  iterations = [],
  liveMarkdown,
  images = [],
  accepted = [],
}: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const [loaded, setLoaded] = useState<IterationSnapshot | null>(null);
  const [loading, setLoading] = useState(false);

  const chosen = selected !== null ? iterations[selected] : null;

  useEffect(() => {
    if (!chosen) {
      setLoaded(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    getIteration(runId, chosen.iteration, chosen.phase)
      .then((item) => {
        if (!cancelled) setLoaded(item);
      })
      .catch(() => {
        if (!cancelled) setLoaded(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [runId, chosen]);

  const previewMd = loaded?.markdown || (selected === null ? liveMarkdown : '');

  return (
    <div className="is-wrap">
      <Header variant="h2">What each pass produced</Header>
      <p className="is-lead">
        Each card is one pipeline step, not a duplicate of the iteration counter. Click a pass to inspect that draft.
      </p>
      <div className="is-cards">
        {iterations.map((item, idx) => {
          const key = `${item.phase}-${item.iteration}-${idx}`;
          const active = selected === idx;
          return (
            <button
              key={key}
              type="button"
              className={`is-card${active ? ' is-active' : ''}`}
              onClick={() => setSelected(idx)}
            >
              <div className="is-card-top">
                <Badge>{item.phase}</Badge>
                <strong>{passLabel(item)}</strong>
              </div>
              <p>{item.summary}</p>
              <dl>
                <div>
                  <dt>Words</dt>
                  <dd>{item.word_count || '—'}</dd>
                </div>
                <div>
                  <dt>Findings</dt>
                  <dd>{item.open_findings_count}</dd>
                </div>
              </dl>
              {item.excerpt ? <p className="is-excerpt">{item.excerpt}</p> : null}
            </button>
          );
        })}
      </div>
      {chosen && (
        <Container header={<Header variant="h3">Preview of {passLabel(chosen)}</Header>}>
          <SpaceBetween size="m">
            {loading ? <p>Loading that draft…</p> : null}
            {!loading && !previewMd ? (
              <p>
                This older run did not store the full draft for that pass. New jobs keep a preview for every iteration.
                Findings from the pass are still listed below when they were saved.
              </p>
            ) : null}
            {previewMd ? <ArticlePreview markdown={previewMd} images={images} /> : null}
            <FindingsPanel findings={loaded?.findings || []} title="Findings from this pass" />
            <FindingsPanel findings={accepted} title="Accepted leftover findings" />
            <Button onClick={() => setSelected(null)}>Back to cards</Button>
          </SpaceBetween>
        </Container>
      )}
    </div>
  );
}
