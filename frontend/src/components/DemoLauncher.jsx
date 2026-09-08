/**
 * DemoLauncher — one-click buttons that register and start a camera for each
 * clip in backend/demo_videos/. Used to drive the live demo without touching
 * Camera Management.
 */
import { useCallback, useEffect, useState } from 'react';
import { fetchDemoVideos, launchDemoVideo } from '../services/api';

export default function DemoLauncher({ onCamerasChange }) {
  const [videos, setVideos] = useState([]);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      setVideos(await fetchDemoVideos());
      setError('');
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const launch = async (file) => {
    setBusy(file);
    setError('');
    try {
      await launchDemoVideo(file);
      await load();
      if (onCamerasChange) onCamerasChange();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  };

  // Nothing dropped in backend/demo_videos/ yet — stay out of the way.
  if (!videos.length && !error) return null;

  return (
    <div className="bg-surface-container-low border border-outline-variant/30 p-container-padding rounded-sm">
      <div className="flex items-center justify-between mb-2">
        <span className="font-label-caps text-on-surface-variant">DEMO FEEDS</span>
        <span className="text-xs text-on-surface-variant/60">backend/demo_videos/</span>
      </div>

      {error && <div className="text-xs text-error mb-2">{error}</div>}

      <div className="flex flex-wrap gap-2">
        {videos.map((v) => (
          <button
            key={v.file}
            onClick={() => launch(v.file)}
            disabled={busy === v.file}
            className={`px-3 py-2 rounded-sm text-xs font-semibold border transition-colors ${
              v.camera_id
                ? 'border-primary/60 text-primary hover:bg-primary/10'
                : 'border-outline-variant/40 text-on-surface hover:border-primary/50'
            } disabled:opacity-50`}
            title={`${v.file} · ${v.size_mb} MB`}
          >
            {busy === v.file ? 'STARTING…' : `▶ ${v.label}`}
            {v.camera_id ? ` · #${v.camera_id}` : ''}
          </button>
        ))}
      </div>
    </div>
  );
}
