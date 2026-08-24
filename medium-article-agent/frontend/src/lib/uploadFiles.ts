export type FileLike = {
  name: string;
  size: number;
  lastModified: number;
};

export function fileKey(file: FileLike): string {
  return `${file.name}:${file.size}:${file.lastModified}`;
}

export function mergeAttachedFiles<T extends FileLike>(
  current: T[],
  incoming: T[],
): { next: T[]; added: number; skipped: number } {
  const seen = new Set(current.map(fileKey));
  const unique: T[] = [];
  for (const file of incoming) {
    const key = fileKey(file);
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(file);
  }
  return {
    next: [...current, ...unique],
    added: unique.length,
    skipped: incoming.length - unique.length,
  };
}

export function describeMerge(added: number, skipped: number, total: number): string {
  if (!added) {
    return `Those files are already attached (${total} total).`;
  }
  if (skipped) {
    return `Added ${added}, skipped ${skipped} duplicate${skipped === 1 ? '' : 's'} · ${total} attached.`;
  }
  return `Added ${added} file${added === 1 ? '' : 's'} · ${total} attached.`;
}
