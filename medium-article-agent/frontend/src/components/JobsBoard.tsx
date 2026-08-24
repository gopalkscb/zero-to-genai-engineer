import { Badge, Container, Header, Table } from '@cloudscape-design/components';
import type { JobRecord } from '../types';
import './JobsBoard.css';

interface Props {
  jobs: JobRecord[];
  onOpen: (runId: string, view?: 'story' | 'pipeline') => void;
}

function statusColor(status: string): 'blue' | 'green' | 'red' | 'grey' {
  if (status === 'completed') return 'green';
  if (status === 'failed') return 'red';
  if (status === 'paused_hitl' || status === 'running') return 'blue';
  return 'grey';
}

export default function JobsBoard({ jobs, onOpen }: Props) {
  if (!jobs.length) return null;
  return (
    <div className="maa-jobs">
      <Container header={<Header variant="h2">Jobs</Header>}>
        <Table
          variant="embedded"
          wrapLines={false}
          contentDensity="compact"
          columnDefinitions={[
            {
              id: 'title',
              header: 'Request',
              minWidth: 280,
              cell: (job) => (
                <span className="maa-job-title" title={job.title || job.topic_hint || job.run_id}>
                  {job.title || job.topic_hint || job.run_id.slice(0, 8)}
                </span>
              ),
            },
            {
              id: 'status',
              header: 'Status',
              minWidth: 120,
              width: 140,
              cell: (job) => <Badge color={statusColor(job.status)}>{job.status.replaceAll('_', ' ')}</Badge>,
            },
            {
              id: 'iter',
              header: 'Iteration',
              minWidth: 90,
              width: 100,
              cell: (job) => String(job.iteration ?? 0),
            },
            {
              id: 'findings',
              header: 'Findings',
              minWidth: 90,
              width: 100,
              cell: (job) => String(job.open_findings_count ?? 0),
            },
            {
              id: 'links',
              header: 'Open',
              minWidth: 160,
              width: 160,
              cell: (job) => (
                <div className="maa-job-links">
                  <button type="button" className="maa-job-link" onClick={() => onOpen(job.run_id, 'story')}>
                    Story
                  </button>
                  <span className="maa-job-sep">·</span>
                  <button type="button" className="maa-job-link" onClick={() => onOpen(job.run_id, 'pipeline')}>
                    Pipeline
                  </button>
                </div>
              ),
            },
          ]}
          items={jobs}
          empty="No pipeline jobs yet."
        />
      </Container>
    </div>
  );
}
