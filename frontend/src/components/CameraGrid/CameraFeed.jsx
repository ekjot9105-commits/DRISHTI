/**
 * CameraFeed — Displays a single camera's live video feed via WebSocket.
 */
import { useEffect, useRef, useState } from 'react';
import { createCameraWebSocket } from '../../services/api';

export default function CameraFeed({ camera, onExpand }) {
  const [frame, setFrame] = useState(null);
  const [fps, setFps] = useState(0);
  const [status, setStatus] = useState('connecting');
  const [currentTime, setCurrentTime] = useState('');
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const mountedRef = useRef(true);

  const cameraId = camera?.id;
  const cameraStatus = camera?.status;

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + Math.floor(now.getMilliseconds()/100));
    }, 100);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    function cleanup() {
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    }

    function connect() {
      if (!mountedRef.current || !cameraId || cameraStatus !== 'active') {
        setStatus('inactive');
        return;
      }

      cleanup();
      setStatus('connecting');

      const ws = createCameraWebSocket(
        cameraId,
        (data) => {
          if (!mountedRef.current) return;
          if (data.type === 'frame') {
            setFrame(`data:image/jpeg;base64,${data.frame}`);
            setFps(data.fps || 0);
            setStatus('live');
          } else if (data.type === 'status') {
            setStatus(data.status);
          }
        },
        (err) => {
          if (!mountedRef.current) return;
        }
      );

      ws.onclose = (event) => {
        if (!mountedRef.current) return;
        setStatus('error');
        reconnectTimerRef.current = setTimeout(() => {
          if (mountedRef.current && cameraStatus === 'active') {
            connect();
          }
        }, 3000);
      };

      wsRef.current = ws;
    }

    connect();

    return () => {
      mountedRef.current = false;
      cleanup();
    };
  }, [cameraId, cameraStatus]);

  if (!camera) return null;

  const isAlert = status === 'alert';
  const borderColor = isAlert ? 'border-error/50' : 'border-outline-variant/50';
  const headerBg = isAlert ? 'bg-error/5' : 'bg-surface/50';
  const titleColor = isAlert ? 'text-error' : 'text-primary';
  const liveBadgeBg = isAlert ? 'bg-error/20' : 'bg-primary/20';
  const liveBadgeText = isAlert ? 'text-error' : 'text-primary';
  const liveBadgeBorder = isAlert ? 'border-error/50' : 'border-primary/50';

  return (
    <div className={`bg-surface-container-low border ${borderColor} rounded-sm flex flex-col relative group`} onClick={() => onExpand && onExpand(camera)} style={{ cursor: onExpand ? 'pointer' : 'default' }}>
      <div className={`flex justify-between items-center p-2 border-b border-outline-variant/30 ${headerBg}`}>
        <span className={`font-label-caps ${titleColor} tracking-widest flex items-center`}>
          <span className={`material-symbols-outlined text-[14px] mr-1 ${isAlert ? 'animate-pulse' : ''}`} data-icon="videocam">videocam</span>
          {camera.name}
        </span>
        <div className="flex space-x-2 items-center">
          <span className={`font-label-md ${isAlert ? 'text-error/80' : 'text-on-surface-variant'} font-data-display text-[10px]`}>{currentTime}</span>
          <span className={`px-1.5 py-0.5 ${liveBadgeBg} ${liveBadgeText} border ${liveBadgeBorder} font-label-caps text-[9px] rounded-sm flex items-center`}>
            <span className={`w-1 h-1 rounded-full ${isAlert ? 'bg-error animate-ping' : 'bg-primary animate-pulse'} mr-1`}></span> 
            {isAlert ? 'ALERT' : (status === 'live' || status === 'connecting' ? 'LIVE' : status.toUpperCase())}
          </span>
        </div>
      </div>
      
      <div className={`flex-1 relative overflow-hidden bg-black flex items-center justify-center ${isAlert ? 'border-[2px] border-error/30 animate-pulse' : ''} min-h-[250px]`}>
        {status === 'live' && frame ? (
          <img src={frame} alt={camera.name} className="w-full h-full object-contain" />
        ) : (
          <div className="absolute inset-0 w-full h-full opacity-60 mix-blend-screen bg-surface-dim flex flex-col items-center justify-center">
            {status === 'connecting' && <div className="w-16 h-16 border border-primary/30 rounded-full border-t-primary/80 animate-spin" style={{animationDuration: '4s'}}></div>}
            {status === 'inactive' && <span className="text-on-surface-variant font-label-caps mt-2">OFFLINE</span>}
            {status === 'error' && <span className="text-error font-label-caps mt-2">CONNECTION LOST</span>}
          </div>
        )}
        
        <div className="absolute inset-0 border-[0.5px] border-primary/10 m-4 pointer-events-none flex justify-center items-center">
            <div className="absolute text-[8px] font-data-display text-primary/50 bottom-2 right-2">REC // 0{camera.id}</div>
            {status === 'live' && <div className="absolute text-[8px] font-data-display text-primary/50 top-2 left-2">{fps} FPS</div>}
        </div>
      </div>
    </div>
  );
}
