import { useMemo, useState } from 'react';
import { Badge, Box, Button, Container, Header, SpaceBetween, Table } from '@cloudscape-design/components';
import type { Finding } from '../types';

interface Props {
  findings: Finding[];
  title?: string;
  description?: string;
}

const SEVERITY_ORDER: Record<string, number> = { critical: 0, major: 1, minor: 2 };
const PREVIEW_COUNT = 8;

function severityColor(severity: string): 'red' | 'blue' | 'grey' {
  if (severity === 'critical') return 'red';
  if (severity === 'major') return 'blue';
  return 'grey';
}

function countBy(findings: Finding[], key: 'severity' | 'reviewer'): [string, number][] {
  const tally = new Map<string, number>();
  for (const item of findings) {
    const value = String(item[key]);
    tally.set(value, (tally.get(value) || 0) + 1);
  }
  return [...tally.entries()].sort((a, b) => b[1] - a[1]);
}

export default function FindingsPanel({ findings, title = 'Open Findings', description }: Props) {
  const [expanded, setExpanded] = useState(false);

  const sorted = useMemo(
    () =>
      [...findings].sort(
        (a, b) => (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3),
      ),
    [findings],
  );

  if (!findings.length) return null;

  const visible = expanded ? sorted : sorted.slice(0, PREVIEW_COUNT);
  const hidden = sorted.length - visible.length;

  return (
    <Container
      header={
        <Header variant="h3" counter={`(${findings.length})`} description={description}>
          {title}
        </Header>
      }
    >
      <SpaceBetween size="s">
        <Box>
          <SpaceBetween direction="horizontal" size="xs">
            {countBy(sorted, 'severity').map(([severity, count]) => (
              <Badge key={severity} color={severityColor(severity)}>
                {severity} {count}
              </Badge>
            ))}
            {countBy(sorted, 'reviewer').map(([reviewer, count]) => (
              <Badge key={reviewer}>
                {reviewer} {count}
              </Badge>
            ))}
          </SpaceBetween>
        </Box>
        <Table
          variant="embedded"
          contentDensity="compact"
          wrapLines
          columnDefinitions={[
            {
              id: 'severity',
              header: 'Severity',
              width: 110,
              cell: (item) => <Badge color={severityColor(item.severity)}>{item.severity}</Badge>,
            },
            { id: 'reviewer', header: 'Reviewer', width: 120, cell: (item) => item.reviewer },
            { id: 'problem', header: 'Problem', cell: (item) => item.problem },
            { id: 'fix', header: 'Suggested fix', cell: (item) => item.suggested_fix },
          ]}
          items={visible}
        />
        {(hidden > 0 || expanded) && (
          <Button variant="link" onClick={() => setExpanded((prev) => !prev)}>
            {expanded ? 'Show fewer' : `Show all ${sorted.length}`}
          </Button>
        )}
      </SpaceBetween>
    </Container>
  );
}
