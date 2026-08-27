/**
 * CameraFeed — Displays a single camera's live video feed via WebSocket.
 * Receives base64 JPEG frames and renders them.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { createCameraWebSocket } from '../../services/api';

export default function CameraFeed({ camera, onExpand }) {
  const [frame, setFrame] = useState(null);
  const [fps, setFps] = useState(0);
  const [status, setStatus] = useState('connecting');
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    if (!camera || camera.status !== 'active') {
      setStatus('inactive');
      return;
    }

    setStatus('connecting');

    const ws = createCameraWebSocket(
      camera.id,
      (data) => {
        if (data.type === 'frame') {
          setFrame(`data:image/jpeg;base64,${data.frame}`);
          setFps(data.fps || 0);
          setStatus('live');
        } else if (data.type === 'status') {
          setStatus(data.status);
        }
      },
      () => {
        setStatus('error');
        // Auto-reconnect after 3 seconds
        reconnectTimerRef.current = setTimeout(connect, 3000);
      }
    );

    ws.onclose = () => {
      if (camera.status === 'active') {
        reconnectTimerRef.current = setTimeout(connect, 2000);
      }
    };

    wsRef.current = ws;
  }, [camera]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, [connect]);

  if (!camera) {
    return (
      <div className="camera-feed">
        <div className="camera-feed-empty">
          <div className="camera-feed-empty-icon">📹</div>
          <div className="camera-feed-empty-text">No camera assigned</div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`camera-feed ${status === 'alert' ? 'alert' : ''}`}
      onClick={() => onExpand && onExpand(camera)}
      style={{ cursor: onExpand ? 'pointer' : 'default' }}
    >
      {status === 'live' && frame ? (
        <img src={frame} alt={camera.name} />
      ) : (
        <div className="camera-feed-empty">
          <div className="camera-feed-empty-icon">
            {status === 'connecting' ? '⏳' : status === 'error' ? '❌' : '📹'}
          </div>
          <div className="camera-feed-empty-text">
            {status === 'connecting' && 'Connecting...'}
            {status === 'inactive' && 'Camera inactive — Start stream to view'}
            {status === 'error' && 'Connection lost — Reconnecting...'}
          </div>
        </div>
      )}

      {/* Overlay */}
      <div className="camera-feed-overlay">
        <div>
          <div className="camera-feed-name">{camera.name}</div>
          <div className="camera-feed-status">
            <span className={`camera-feed-status-dot ${status === 'live' ? 'live' : 'offline'}`}></span>
            {camera.location || camera.source_type.toUpperCase()}
          </div>
        </div>
      </div>

      {/* Live badge */}
      {status === 'live' && (
        <div className="camera-feed-badge live">● LIVE</div>
      )}

      {/* FPS counter */}
      {status === 'live' && (
        <div className="camera-feed-fps">{fps} FPS</div>
      )}
    </div>
  );
}
