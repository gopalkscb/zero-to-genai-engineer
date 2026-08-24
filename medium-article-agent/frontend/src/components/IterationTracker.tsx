import { Box, Container, Header, ProgressBar } from '@cloudscape-design/components';

interface Props {
  iteration: number;
  maxIterations?: number;
}

export default function IterationTracker({ iteration, maxIterations = 5 }: Props) {
  const pct = Math.min(100, (iteration / maxIterations) * 100);
  return (
    <Container header={<Header variant="h3">Review Iterations</Header>}>
      <Box variant="p">Iteration {iteration} of {maxIterations}</Box>
      <ProgressBar value={pct} label="Review progress" />
    </Container>
  );
}
