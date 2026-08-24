import { Container, Header, Table } from '@cloudscape-design/components';
import type { LogEntry } from '../types';

interface Props {
  logs: LogEntry[];
}

export default function LogFeed({ logs }: Props) {
  return (
    <Container header={<Header variant="h3">Live Log Feed</Header>}>
      <Table
        columnDefinitions={[
          { id: 'time', header: 'Time', cell: (item) => item.timestamp?.slice(11, 19) ?? '' },
          { id: 'node', header: 'Node', cell: (item) => item.node },
          { id: 'level', header: 'Level', cell: (item) => item.level },
          { id: 'message', header: 'Message', cell: (item) => item.message },
        ]}
        items={logs.slice().reverse()}
        empty="Waiting for pipeline events..."
      />
    </Container>
  );
}
