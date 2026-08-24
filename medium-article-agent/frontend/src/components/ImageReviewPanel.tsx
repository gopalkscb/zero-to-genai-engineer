import { Badge, Box, Container, Header } from '@cloudscape-design/components';
import type { ImageAsset } from '../types';

interface Props {
  images?: ImageAsset[];
}

export default function ImageReviewPanel({ images = [] }: Props) {
  if (!images.length) return null;
  return (
    <Container header={<Header variant="h2">Image review</Header>}>
      <p style={{ marginTop: 0, color: '#5c574e' }}>
        Figures are generated first, then an art-direction node accepts or rejects them. Rejected
        images are redrawn and reviewed again, up to two times, before the article reviewers start.
      </p>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {images.map((image) => (
          <li
            key={image.image_id}
            style={{
              display: 'grid',
              gridTemplateColumns: '160px 1fr',
              gap: 16,
              padding: '12px 0',
              borderBottom: '1px solid #e9ebed',
            }}
          >
            {image.url && image.status === 'generated' ? (
              <img src={image.url} alt={image.caption || image.prompt} style={{ width: '100%', borderRadius: 8 }} />
            ) : (
              <Box color="text-status-inactive">No image</Box>
            )}
            <div>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                <strong>{image.image_id}</strong>
                <Badge
                  color={
                    image.review_notes?.startsWith('Awaiting')
                      ? 'grey'
                      : image.review_passed === false
                        ? 'red'
                        : 'green'
                  }
                >
                  {image.review_notes?.startsWith('Awaiting')
                    ? 'Pending review'
                    : image.review_passed === false
                      ? 'Redraw required'
                      : 'Passed review'}
                </Badge>
                <Badge>{image.status}</Badge>
              </div>
              <p style={{ margin: '0 0 6px' }}>{image.caption || image.prompt}</p>
              {image.review_notes ? (
                <p style={{ margin: 0, color: '#5c574e' }}>{image.review_notes}</p>
              ) : (
                <p style={{ margin: 0, color: '#5c574e' }}>No reviewer notes on this figure.</p>
              )}
            </div>
          </li>
        ))}
      </ul>
    </Container>
  );
}
