/**
 * CameraGrid — Multi-camera mosaic view for the Command Center.
 */
import CameraFeed from './CameraFeed';

export default function CameraGrid({ cameras, onExpandCamera }) {
  if (!cameras || cameras.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-surface-container-low border border-outline-variant/30 rounded-sm min-h-[400px]">
        <div className="flex flex-col items-center text-on-surface-variant">
          <span className="material-symbols-outlined text-4xl mb-2" style={{fontVariationSettings: "'FILL' 1"}}>videocam_off</span>
          <span className="font-label-caps">No cameras configured</span>
        </div>
      </div>
    );
  }

  // Use a responsive grid based on camera count
  const gridClass = cameras.length === 1 ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2';

  return (
    <div className={`grid ${gridClass} gap-gutter`}>
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
