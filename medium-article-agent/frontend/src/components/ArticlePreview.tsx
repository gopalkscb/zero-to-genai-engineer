import React from 'react';
import type { Components } from 'react-markdown';
import ReactMarkdown from 'react-markdown';
import type { ImageAsset } from '../types';
import './ArticlePreview.css';

interface Props {
  markdown: string;
  images?: ImageAsset[];
  subtitle?: string;
  tags?: string[];
}

function Figure({ src, alt }: { src?: string; alt?: string }) {
  if (!src || src.includes('example.com')) return null;
  return (
    <figure className="medium-figure">
      <img src={src} alt={alt || ''} />
      {alt ? <figcaption>{alt}</figcaption> : null}
    </figure>
  );
}

function isItalicEcho(children: React.ReactNode, caption: string): boolean {
  if (!caption) return false;
  const items = React.Children.toArray(children);
  if (items.length !== 1 || !React.isValidElement(items[0])) return false;
  const child = items[0] as React.ReactElement<{ children?: React.ReactNode }>;
  const tag = child.type;
  if (tag !== 'em' && tag !== 'i') return false;
  const text = String(child.props.children ?? '').trim();
  return text === caption.trim();
}

function unwrapOuterFence(markdown: string): string {
  const stripped = markdown.trim();
  if (!stripped.startsWith('```')) return stripped;
  const newline = stripped.indexOf('\n');
  if (newline === -1) return stripped;
  const lang = stripped.slice(3, newline).trim().toLowerCase();
  if (lang && lang !== 'markdown' && lang !== 'md') return stripped;
  let body = stripped.slice(newline + 1);
  if (/\n```\s*$/.test(body)) {
    body = body.replace(/\n```\s*$/, '');
  }
  return body.trim();
}

function stripFakeImages(markdown: string): string {
  return unwrapOuterFence(markdown)
    .replace(/!\[[^\]]*\]\(https?:\/\/(?:example\.com|via\.placeholder\.com)[^)]*\)(?:\n+\*[^*\n]+\*)?/gi, '')
    .replace(/\n{3,}/g, '\n\n');
}

function collapseCaptionLines(markdown: string): string {
  return markdown.replace(/!\[([^\]]*)\]\(([^)]+)\)\n+\*([^*\n]+)\*/g, (_m, alt, url, cap) => {
    return `![${alt || cap}](${url})`;
  });
}

function withInjectedImages(markdown: string, images: ImageAsset[]): string {
  const ready = images.filter((img) => img.status === 'generated' && img.url);
  if (!ready.length) return markdown;
  if (ready.some((img) => img.url && markdown.includes(img.url))) return markdown;
  const hero = ready[0];
  const heroBlock = `\n\n![${hero.caption || hero.prompt}](${hero.url})\n\n`;
  const h1 = markdown.indexOf('# ');
  if (h1 === -1) return heroBlock + markdown;
  const headingEnd = markdown.indexOf('\n', h1);
  if (headingEnd === -1) return markdown + heroBlock;
  let next = `${markdown.slice(0, headingEnd)}\n${heroBlock}${markdown.slice(headingEnd)}`;
  if (ready[1]) {
    const firstH2 = next.indexOf('\n## ');
    const secondH2 = firstH2 === -1 ? -1 : next.indexOf('\n## ', firstH2 + 1);
    if (secondH2 !== -1) {
      const lineEnd = next.indexOf('\n', secondH2 + 1);
      next = `${next.slice(0, lineEnd)}\n\n![${ready[1].caption || ready[1].prompt}](${ready[1].url})\n${next.slice(lineEnd)}`;
    }
  }
  return next;
}

function readMinutes(markdown: string): number {
  const words = markdown.replace(/[#>*_`\[\]()!]/g, ' ').split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / 220));
}

function childText(node: React.ReactNode): string {
  return React.Children.toArray(node)
    .map((child) => {
      if (typeof child === 'string' || typeof child === 'number') return String(child);
      if (React.isValidElement(child)) {
        const props = child.props as { children?: React.ReactNode };
        return childText(props.children);
      }
      return '';
    })
    .join('');
}

function extractSubtitle(markdown: string, provided?: string): { subtitle: string; rest: string } {
  let rest = markdown;
  let subtitle = (provided || '').trim();
  const ital = rest.match(/^#\s+.+\n+\*([^*\n]+)\*\n+/);
  if (ital) {
    if (!subtitle) subtitle = ital[1].trim();
    rest = rest.replace(`\n*${ital[1]}*`, '');
  }
  rest = rest.replace(/^#\s+.+\n+/, '');
  return { subtitle, rest };
}

export default function ArticlePreview({ markdown, images = [], subtitle = '', tags = [] }: Props) {
  const prepared = collapseCaptionLines(stripFakeImages(withInjectedImages(markdown, images)));
  const titleMatch = prepared.match(/^#\s+(.+)$/m);
  const title = titleMatch?.[1] ?? 'Medium Preview';
  const pulled = extractSubtitle(prepared, subtitle);
  const minutes = prepared ? readMinutes(prepared) : 1;
  let lastCaption = '';

  const components: Components = {
    img: ({ src, alt }) => {
      lastCaption = alt || '';
      return <Figure src={src} alt={alt} />;
    },
    p: ({ children, node }) => {
      const kids = (node?.children ?? []) as { tagName?: string }[];
      if (kids.length === 1 && kids[0]?.tagName === 'img') {
        return <>{children}</>;
      }
      if (isItalicEcho(children, lastCaption)) return null;
      const disclosure = /ai assistance/i.test(childText(children));
      return <p className={disclosure ? 'medium-disclosure' : undefined}>{children}</p>;
    },
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noreferrer">
        {children}
      </a>
    ),
  };

  return (
    <div className="medium-stage">
      <article className="medium-story">
        {prepared ? (
          <>
            <header className="medium-meta">
              <div className="medium-avatar" aria-hidden="true">
                MA
              </div>
              <div>
                <div className="medium-author">Medium Article Agent</div>
                <div className="medium-byline">Draft preview · {minutes} min read</div>
              </div>
            </header>
            <h1>{title}</h1>
            {pulled.subtitle ? <p className="medium-subtitle">{pulled.subtitle}</p> : null}
            {tags.length ? (
              <div className="medium-tags">
                {tags.slice(0, 5).map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            ) : null}
            <div className="medium-body">
              <ReactMarkdown components={components}>{pulled.rest}</ReactMarkdown>
            </div>
            <footer className="medium-footer">
              Preview of “{title}”. Copy from Review & export when you are ready to paste into Medium.
            </footer>
          </>
        ) : (
          <p className="medium-empty">The article preview will appear here once the draft is ready.</p>
        )}
      </article>
    </div>
  );
}
