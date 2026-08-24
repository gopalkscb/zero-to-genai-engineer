import { afterEach, describe, expect, it, vi } from 'vitest';
import { startPipeline, resumeRun } from './client';

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('startPipeline', () => {
  it('posts every attached file under the files field', async () => {
    const sent: FormData[] = [];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url: string, init?: RequestInit) => {
        sent.push(init?.body as FormData);
        return new Response(JSON.stringify({ run_id: 'run-1', status: 'running' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }),
    );

    const files = [
      new File(['alpha'], 'alpha.txt', { type: 'text/plain' }),
      new File(['beta'], 'beta.txt', { type: 'text/plain' }),
    ];
    const result = await startPipeline(files, 'two sources', false);

    expect(result.run_id).toBe('run-1');
    const form = sent[0];
    expect(form.get('topic_hint')).toBe('two sources');
    expect(form.get('enable_web_research')).toBe('false');
    const uploaded = form.getAll('files');
    expect(uploaded).toHaveLength(2);
    expect((uploaded[0] as File).name).toBe('alpha.txt');
    expect((uploaded[1] as File).name).toBe('beta.txt');
  });

  it('posts resume to the run endpoint', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string) => {
        expect(url).toBe('/api/pipeline/run-9/resume');
        return new Response(
          JSON.stringify({
            run_id: 'run-9',
            status: 'running',
            resumed: true,
            next_nodes: ['image_gen'],
            detail: 'Resuming at image_gen',
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } },
        );
      }),
    );
    const result = await resumeRun('run-9');
    expect(result.resumed).toBe(true);
    expect(result.next_nodes).toEqual(['image_gen']);
  });
});
