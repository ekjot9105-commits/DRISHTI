/**
 * CameraGrid — Multi-camera mosaic view for the Command Center.
 * Automatically adjusts grid layout based on camera count.
 */
import CameraFeed from './CameraFeed';

function getGridClass(count) {
  if (count <= 1) return 'grid-1';
  if (count <= 2) return 'grid-2';
  if (count <= 4) return 'grid-4';
  if (count <= 6) return 'grid-6';
  return 'grid-9';
}

export default function CameraGrid({ cameras, onExpandCamera }) {
  if (!cameras || cameras.length === 0) {
    return (
      <div className="camera-grid grid-1">
        <div className="camera-feed">
          <div className="camera-feed-empty">
            <div className="camera-feed-empty-icon">📡</div>
            <div className="camera-feed-empty-text">No cameras configured</div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
              Go to Camera Management to add your first camera
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`camera-grid ${getGridClass(cameras.length)}`}>
      {cameras.map((camera) => (
        <CameraFeed
          key={camera.id}
          camera={camera}
          onExpand={onExpandCamera}
        />
      ))}
    </div>
  );
}
