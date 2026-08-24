import { describe, expect, it } from 'vitest';
import { describeMerge, fileKey, mergeAttachedFiles } from './uploadFiles';

function fakeFile(name: string, size = 12, lastModified = 1) {
  return { name, size, lastModified };
}

describe('mergeAttachedFiles', () => {
  it('appends a second file instead of replacing the first', () => {
    const first = fakeFile('notes.md', 40);
    const second = fakeFile('deck.pptx', 80);
    const result = mergeAttachedFiles([first], [second]);
    expect(result.next.map((file) => file.name)).toEqual(['notes.md', 'deck.pptx']);
    expect(result.added).toBe(1);
    expect(result.skipped).toBe(0);
  });

  it('keeps both files from a multi-select', () => {
    const result = mergeAttachedFiles([], [fakeFile('a.txt'), fakeFile('b.txt')]);
    expect(result.next).toHaveLength(2);
    expect(result.added).toBe(2);
  });

  it('skips a duplicate by name, size, and timestamp', () => {
    const existing = fakeFile('notes.md', 40, 99);
    const result = mergeAttachedFiles([existing], [fakeFile('notes.md', 40, 99)]);
    expect(result.next).toHaveLength(1);
    expect(result.added).toBe(0);
    expect(result.skipped).toBe(1);
  });

  it('keeps same-name files when the bytes differ', () => {
    const result = mergeAttachedFiles(
      [fakeFile('notes.md', 40, 1)],
      [fakeFile('notes.md', 80, 2)],
    );
    expect(result.next).toHaveLength(2);
    expect(result.added).toBe(1);
  });

  it('does not drop earlier files when adding a batch that includes a duplicate', () => {
    const a = fakeFile('a.txt');
    const b = fakeFile('b.txt');
    const result = mergeAttachedFiles([a], [a, b]);
    expect(result.next.map((file) => file.name)).toEqual(['a.txt', 'b.txt']);
    expect(result.added).toBe(1);
    expect(result.skipped).toBe(1);
  });
});

describe('describeMerge', () => {
  it('reports a clean add', () => {
    expect(describeMerge(2, 0, 3)).toBe('Added 2 files · 3 attached.');
    expect(describeMerge(1, 0, 1)).toBe('Added 1 file · 1 attached.');
  });

  it('reports skipped duplicates', () => {
    expect(describeMerge(1, 1, 2)).toBe('Added 1, skipped 1 duplicate · 2 attached.');
    expect(describeMerge(0, 2, 2)).toBe('Those files are already attached (2 total).');
  });
});

describe('fileKey', () => {
  it('is stable for the same file identity', () => {
    const file = fakeFile('a.txt', 10, 5);
    expect(fileKey(file)).toBe(fileKey({ ...file }));
  });
});
