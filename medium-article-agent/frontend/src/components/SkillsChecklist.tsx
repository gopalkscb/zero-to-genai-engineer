import type { SkillsAudit } from '../types';
import './SkillsChecklist.css';

interface Props {
  audit?: SkillsAudit;
}

export default function SkillsChecklist({ audit }: Props) {
  const checks = audit?.checks || [];
  if (!checks.length) return null;
  const failed = audit?.failed ?? checks.filter((item) => !item.passed).length;
  const passed = audit?.passed ?? checks.length - failed;

  return (
    <section className="sk-panel">
      <header className="sk-head">
        <div>
          <p className="sk-kicker">backend/skills/medium.md</p>
          <h3>House skill gate</h3>
        </div>
        <p className={`sk-score${failed ? ' is-open' : ''}`}>
          {passed} passed · {failed} open
          {audit?.word_count ? ` · ${audit.word_count} words` : ''}
        </p>
      </header>
      <ul className="sk-list">
        {checks.map((item) => (
          <li key={item.id} className={item.passed ? 'is-pass' : 'is-fail'}>
            <span className="sk-mark" aria-hidden="true">
              {item.passed ? '✓' : '!'}
            </span>
            <div>
              <strong>{item.label}</strong>
              {item.detail ? <p>{item.detail}</p> : null}
              {!item.passed && item.suggested_fix ? <p className="sk-fix">{item.suggested_fix}</p> : null}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
