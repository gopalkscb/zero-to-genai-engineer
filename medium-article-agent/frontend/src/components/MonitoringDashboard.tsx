import { Badge, Box, Button, ColumnLayout, Container, Header, Link, SpaceBetween } from '@cloudscape-design/components';
import type { RunStatus } from '../types';

interface Props {
  status: RunStatus | null;
  onResume?: () => void;
  resuming?: boolean;
}

export default function MonitoringDashboard({ status, onResume, resuming }: Props) {
  if (!status) return null;
  const running = status.status === 'running';
  return (
    <Container header={<Header variant="h2">{status.title || 'Pipeline job'}</Header>}>
      <ColumnLayout columns={6}>
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Status</Box>
          <Badge color={status.status === 'completed' ? 'green' : 'blue'}>{status.status}</Badge>
        </SpaceBetween>
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Iteration</Box>
          <Box>
            {status.iteration} / {status.max_iterations ?? 10}
          </Box>
        </SpaceBetween>
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Resolved</Box>
          <Box>{status.resolved_findings_count ?? 0}</Box>
        </SpaceBetween>
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Open findings</Box>
          <Box>
            {status.open_findings_count}
            {status.blocking_findings_count !== undefined && (
              <Box variant="span" color="text-body-secondary">
                {' '}
                ({status.blocking_findings_count} blocking)
              </Box>
            )}
          </Box>
        </SpaceBetween>
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">{running ? 'Working on' : 'Last node'}</Box>
          <Box>{status.last_node || '—'}</Box>
        </SpaceBetween>
        <SpaceBetween size="xs">
          <Box variant="awsui-key-label">Editor score</Box>
          <Box>{status.editor_score ? `${Number(status.editor_score).toFixed(1)} / 10` : '—'}</Box>
        </SpaceBetween>
      </ColumnLayout>
      {status.progress_hint && running ? (
        <Box margin={{ top: 's' }} color="text-status-info">
          {status.progress_hint}
        </Box>
      ) : null}
      <Box margin={{ top: 's' }}>
        <SpaceBetween direction="horizontal" size="s">
          <Link href={status.preview_url || `/?run=${status.run_id}`}>Story page</Link>
          <Link href={status.pipeline_url || `/?run=${status.run_id}&view=pipeline`}>Pipeline demo</Link>
          {running && onResume ? (
            <Button onClick={onResume} loading={resuming}>
              Resume graph
            </Button>
          ) : null}
        </SpaceBetween>
      </Box>
      {status.editor_notes ? (
        <Box margin={{ top: 's' }} color="text-body-secondary">
          Editor: {status.editor_notes}
        </Box>
      ) : null}
      {status.cap_hit_with_open_findings && (
        <Box margin={{ top: 's' }} color="text-status-warning">
          Review cap reached. Leftover findings are kept as accepted findings instead of being dropped.
        </Box>
      )}
      {status.stalled && !status.cap_hit_with_open_findings && (
        <Box margin={{ top: 's' }} color="text-status-warning">
          Loop exited early: two passes resolved nothing and the rewrite stopped changing the draft.
          The remaining findings were accepted rather than burning the rest of the iteration budget.
        </Box>
      )}
      {status.error && (
        <Box margin={{ top: 's' }} color="text-status-error">
          {status.error}
        </Box>
      )}
    </Container>
  );
}
