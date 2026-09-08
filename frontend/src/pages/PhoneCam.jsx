/**
 * PhoneCam — turns a phone (or any device with a camera) into a DRISHTI feed.
 *
 * Opened at /phone, usually by scanning the QR code on the Camera Management
 * page. It registers a phone-source camera, grabs the rear camera via
 * getUserMedia, and pushes JPEG frames over a WebSocket to the backend, where
 * they run through the same detection pipeline as any CCTV feed.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { registerPhoneCamera, createPushWebSocket } from '../services/api';

const TARGET_FPS = 12;
const JPEG_QUALITY = 0.6;

export default function PhoneCam() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);

  const [status, setStatus] = useState('idle'); // idle | starting | live | error
  const [error, setError] = useState('');
  const [cameraId, setCameraId] = useState(null);
  const [framesSent, setFramesSent] = useState(0);

  const stop = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setStatus('idle');
  }, []);

  // Always release the camera when the page goes away.
  useEffect(() => stop, [stop]);

  const start = async () => {
    setError('');
    setStatus('starting');
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('Camera access needs a secure context (https:// or localhost).');
      }

      // 1. Claim a camera slot on the backend (reuse it across restarts).
      let id = cameraId;
      if (!id) {
        const params = new URLSearchParams(window.location.search);
        const preset = params.get('cam');
        if (preset) {
          id = Number(preset);
        } else {
          const created = await registerPhoneCamera(
            params.get('name') || `Phone ${new Date().toLocaleTimeString()}`,
          );
          id = created.camera_id;
        }
        setCameraId(id);
      }

      // 2. Rear camera where available.
      const media = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'environment' }, width: 1280, height: 720 },
        audio: false,
      });
      streamRef.current = media;
      videoRef.current.srcObject = media;
      await videoRef.current.play();

      // 3. Push JPEG frames.
      const ws = createPushWebSocket(id);
      wsRef.current = ws;

      ws.onopen = () => {
        setStatus('live');
        const canvas = canvasRef.current;
        timerRef.current = setInterval(() => {
          const video = videoRef.current;
          if (!video || ws.readyState !== WebSocket.OPEN || !video.videoWidth) return;
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
          canvas.toBlob(
            (blob) => {
              if (!blob || ws.readyState !== WebSocket.OPEN) return;
              // Drop frames instead of queueing if the link is congested.
              if (ws.bufferedAmount > 512 * 1024) return;
              blob.arrayBuffer().then((buf) => {
                ws.send(buf);
                setFramesSent((n) => n + 1);
              });
            },
            'image/jpeg',
            JPEG_QUALITY,
          );
        }, 1000 / TARGET_FPS);
      };

      ws.onerror = () => {
        setError('Lost connection to the DRISHTI backend.');
        setStatus('error');
      };
      ws.onclose = () => {
        if (timerRef.current) clearInterval(timerRef.current);
        setStatus('idle');
      };
    } catch (e) {
      setError(e.message || String(e));
      setStatus('error');
      stop();
    }
  };

  const statusColor = { live: '#22c55e', starting: '#eab308', error: '#ef4444', idle: '#64748b' }[status];

  return (
    <div style={{ minHeight: '100vh', background: '#0b0f14', color: '#e2e8f0',
                  fontFamily: 'system-ui, sans-serif', padding: 16 }}>
      <div style={{ maxWidth: 520, margin: '0 auto' }}>
        <h1 style={{ fontSize: 20, letterSpacing: 2, margin: '8px 0 4px' }}>DRISHTI · PHONE CAMERA</h1>
        <p style={{ color: '#94a3b8', fontSize: 13, marginTop: 0 }}>
          This device becomes a live surveillance feed. Keep the screen on.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '12px 0' }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: statusColor }} />
          <strong style={{ textTransform: 'uppercase', fontSize: 12 }}>{status}</strong>
          {cameraId != null && <span style={{ fontSize: 12, color: '#94a3b8' }}>· camera #{cameraId}</span>}
          {status === 'live' && <span style={{ fontSize: 12, color: '#94a3b8' }}>· {framesSent} frames</span>}
        </div>

        <video
          ref={videoRef}
          playsInline
          muted
          style={{ width: '100%', borderRadius: 8, background: '#000', aspectRatio: '16/9' }}
        />
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {error && (
          <div style={{ background: '#7f1d1d', padding: 10, borderRadius: 6, marginTop: 12, fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
          <button
            onClick={start}
            disabled={status === 'live' || status === 'starting'}
            style={{ flex: 1, padding: '14px 0', border: 0, borderRadius: 6, fontWeight: 700,
                     background: status === 'live' ? '#1e293b' : '#22d3ee', color: '#04202b' }}
          >
            {status === 'live' ? 'STREAMING' : 'GO LIVE'}
          </button>
          <button
            onClick={stop}
            disabled={status !== 'live'}
            style={{ flex: 1, padding: '14px 0', border: '1px solid #475569', borderRadius: 6,
                     fontWeight: 700, background: 'transparent', color: '#e2e8f0' }}
          >
            STOP
          </button>
        </div>

        <p style={{ color: '#64748b', fontSize: 12, marginTop: 16 }}>
          This page is served over HTTPS with a self-signed certificate, which is
          what lets the browser grant camera access on a LAN address. The first
          time you open it your phone will warn that the connection is not
          private — choose Advanced and continue to accept it.
        </p>
      </div>
    </div>
  );
}
