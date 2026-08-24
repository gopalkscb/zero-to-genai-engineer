import { useEffect, useRef, useState } from 'react';
import { getConfig, startPipeline } from '../api/client';
import { describeMerge, mergeAttachedFiles } from '../lib/uploadFiles';
import type { ConfigStatus } from '../types';
import './UploadPanel.css';

interface Props {
  onStarted: (runId: string) => void;
}

type PickerWindow = Window & {
  showOpenFilePicker?: (options?: { multiple?: boolean }) => Promise<unknown>;
};

const SAMPLE = `# Byte Pair Encoding

Byte Pair Encoding (BPE) is the tokenizer behind GPT-style models.
It starts from characters and repeatedly merges the most common pair
until it hits a vocabulary budget. That is why "unhappiness" can
become tokens like "un", "happiness" instead of one unknown word.
`;

function environmentReport(): string {
  const w = window as PickerWindow;
  const parts = [
    `framed=${window.top === window.self ? 'no' : 'yes'}`,
    `secure=${window.isSecureContext ? 'yes' : 'no'}`,
    `fsApi=${typeof w.showOpenFilePicker === 'function' ? 'yes' : 'no'}`,
  ];
  return parts.join(' · ');
}

export default function UploadPanel({ onStarted }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [topicHint, setTopicHint] = useState('');
  const [pasted, setPasted] = useState('');
  const [enableWebResearch, setEnableWebResearch] = useState(false);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [diag, setDiag] = useState('');
  const [config, setConfig] = useState<ConfigStatus | null>(null);

  useEffect(() => {
    getConfig().then(setConfig).catch(() => {});
  }, []);

  const applyFiles = (incoming: FileList | File[] | null) => {
    const added = Array.from(incoming || []);
    if (!added.length) return;
    setFiles((prev) => {
      const { next, added: addedCount, skipped } = mergeAttachedFiles(prev, added);
      setDiag(describeMerge(addedCount, skipped, next.length));
      return next;
    });
    setError('');
  };

  // One visible button. The native input is hidden and clicked here so Chrome
  // does not paint a second "Choose File" control next to it.
  const openPicker = () => {
    const stamp = new Date().toLocaleTimeString();
    setError('');
    setDiag(`${stamp} — opening picker (${environmentReport()})`);
    inputRef.current?.click();
  };

  const usePastedText = () => {
    const text = pasted.trim();
    if (text.length < 20) {
      setError('Paste at least a short paragraph, then click Use pasted text.');
      return;
    }
    applyFiles([new File([text], 'pasted-source.txt', { type: 'text/plain' })]);
  };

  const useSample = () => {
    applyFiles([new File([SAMPLE], 'sample-source.txt', { type: 'text/plain' })]);
  };

  const handleStart = async () => {
    if (!files.length) {
      setError('Add a source first: choose a file, drop one, paste text, or use the sample.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const { run_id } = await startPipeline(files, topicHint, enableWebResearch);
      onStarted(run_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="maa-upload">
      <h2>Upload Sources</h2>
      {config && (
        <p className="maa-upload-meta">
          Style guide: {config.style_guide.loaded ? 'Loaded' : 'Missing'}
        </p>
      )}
      <p className="maa-upload-note">
        Exports Medium-ready Markdown and HTML. Does not auto-publish to Medium.
      </p>

      <div className="maa-picker-row">
        <button type="button" className="maa-btn maa-btn-choose" onClick={openPicker}>
          {files.length ? 'Add more files' : 'Choose files'}
        </button>
        <input
          ref={inputRef}
          id="maa-source-file"
          className="maa-file"
          type="file"
          multiple
          hidden
          aria-hidden="true"
          tabIndex={-1}
          data-testid="maa-source-file"
          accept=".pdf,.pptx,.html,.htm,.ipynb,.txt,.md,.markdown,.csv"
          onChange={(event) => {
            applyFiles(event.target.files);
            event.currentTarget.value = '';
          }}
        />
      </div>
      {diag && <p className="maa-diag">{diag}</p>}

      <div
        className={`maa-drop${dragging ? ' is-drag' : ''}`}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          applyFiles(event.dataTransfer.files);
        }}
      >
        <strong>Or drop PDF, PPTX, HTML, notebook, or text files here</strong>
        <span>Select several at once, or add more after the first. Drag from Finder works too.</span>
      </div>

      <label className="maa-field-label" htmlFor="maa-paste">
        Or paste source text
      </label>
      <textarea
        id="maa-paste"
        className="maa-paste"
        rows={7}
        value={pasted}
        onChange={(event) => setPasted(event.target.value)}
        placeholder="Paste a transcript, notes, or article source here…"
      />
      <div className="maa-upload-actions">
        <button type="button" className="maa-btn" onClick={usePastedText}>
          Use pasted text
        </button>
        <button type="button" className="maa-btn" onClick={useSample}>
          Use sample source
        </button>
      </div>

      {files.length > 0 && (
        <div className="maa-file-list">
          <p className="maa-file-count">
            {files.length} source{files.length === 1 ? '' : 's'} attached
          </p>
          <ul className="maa-file-tokens">
            {files.map((file, index) => (
              <li key={`${file.name}-${file.size}-${index}`}>
                <span>
                  {file.name}
                  <em>{(file.size / 1024).toFixed(1)} KB</em>
                </span>
                <button
                  type="button"
                  className="maa-file-remove"
                  onClick={() => setFiles((prev) => prev.filter((_, i) => i !== index))}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
          <button type="button" className="maa-file-clear" onClick={() => setFiles([])}>
            Clear all
          </button>
        </div>
      )}

      <label className="maa-field-label" htmlFor="maa-topic">
        Topic hint
      </label>
      <input
        id="maa-topic"
        className="maa-text"
        value={topicHint}
        onChange={(event) => setTopicHint(event.target.value)}
        placeholder="e.g. LangGraph for editorial pipelines"
      />

      <label className="maa-check">
        <input
          type="checkbox"
          checked={enableWebResearch}
          onChange={(event) => setEnableWebResearch(event.target.checked)}
        />
        Enable web research (DuckDuckGo, optional citations only)
      </label>

      {error && <p className="maa-error">{error}</p>}

      <button type="button" className="maa-btn maa-btn-primary" disabled={loading} onClick={handleStart}>
        {loading ? 'Starting…' : 'Start Pipeline'}
      </button>
    </section>
  );
}
