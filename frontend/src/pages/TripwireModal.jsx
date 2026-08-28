import React, { useState, useEffect, useRef } from 'react';
import { WS_BASE } from '../services/api';

export default function TripwireModal({ camera, onClose }) {
  const [points, setPoints] = useState([]);
  const [saving, setSaving] = useState(false);
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  
  useEffect(() => {
    // If there's an existing tripwire, load it
    if (camera.tripwire_line) {
      try {
        const parsed = JSON.parse(camera.tripwire_line);
        if (parsed.length === 2) {
          setPoints(parsed);
        }
      } catch (e) { }
    }
  }, [camera]);

  useEffect(() => {
    // Connect to WS to get a frame for drawing reference
    const ws = new WebSocket(`${WS_BASE}/ws/camera/${camera.id}`);
    ws.onmessage = (event) => {
      if (imgRef.current) {
        const data = JSON.parse(event.data);
        if (data.frame) {
          imgRef.current.src = `data:image/jpeg;base64,${data.frame}`;
        }
      }
    };
    return () => ws.close();
  }, [camera.id]);

  useEffect(() => {
    drawCanvas();
  }, [points]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (points.length > 0) {
      ctx.beginPath();
      ctx.arc(points[0].x * canvas.width, points[0].y * canvas.height, 5, 0, 2 * Math.PI);
      ctx.fillStyle = 'red';
      ctx.fill();
    }
    
    if (points.length === 2) {
      ctx.beginPath();
      ctx.arc(points[1].x * canvas.width, points[1].y * canvas.height, 5, 0, 2 * Math.PI);
      ctx.fillStyle = 'red';
      ctx.fill();
      
      ctx.beginPath();
      ctx.moveTo(points[0].x * canvas.width, points[0].y * canvas.height);
      ctx.lineTo(points[1].x * canvas.width, points[1].y * canvas.height);
      ctx.strokeStyle = 'red';
      ctx.lineWidth = 3;
      ctx.stroke();
    }
  };

  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    
    if (points.length === 2) {
      // Reset if already 2 points
      setPoints([{x, y}]);
    } else {
      setPoints([...points, {x, y}]);
    }
  };

  const handleSave = async () => {
    if (points.length !== 2) return;
    setSaving(true);
    try {
      const { API_BASE } = await import('../services/api');
      await fetch(`${API_BASE}/api/cameras/${camera.id}/tripwire`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tripwire_line: JSON.stringify(points) })
      });
      onClose(true); // Tell parent to reload
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleClear = async () => {
    setPoints([]);
    setSaving(true);
    try {
      const { API_BASE } = await import('../services/api');
      await fetch(`${API_BASE}/api/cameras/${camera.id}/tripwire`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tripwire_line: "" })
      });
      onClose(true);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-[#0b101e] border border-[#1e293b] rounded-lg w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col">
        <div className="p-4 border-b border-[#1e293b] flex justify-between items-center bg-[#0f172a]">
          <h3 className="font-bold tracking-wider text-cyan-500">
            DRAW VIRTUAL TRIPWIRE - {camera.name}
          </h3>
          <button className="text-slate-400 hover:text-white" onClick={() => onClose(false)}>
            ✕
          </button>
        </div>
        
        <div className="p-4 flex-1 flex flex-col bg-black">
          <p className="text-sm text-slate-400 mb-4 uppercase tracking-widest text-center">
            Click exactly two points on the video to define the intrusion perimeter line.
          </p>
          
          <div className="relative mx-auto border border-[#1e293b] w-full max-w-3xl aspect-video bg-[#1e293b]/20">
            {camera.status === 'active' ? (
              <>
                <img ref={imgRef} className="absolute inset-0 w-full h-full object-contain" alt="Live Feed" />
                <canvas 
                  ref={canvasRef} 
                  className="absolute inset-0 w-full h-full cursor-crosshair z-10"
                  width={800} 
                  height={450} 
                  onClick={handleCanvasClick}
                />
              </>
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                Camera must be ACTIVE to draw a tripwire.
              </div>
            )}
          </div>
        </div>

        <div className="p-4 border-t border-[#1e293b] flex justify-between bg-[#0f172a]">
          <button onClick={handleClear} className="px-4 py-2 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition">
            CLEAR
          </button>
          <div className="flex gap-3">
            <button onClick={() => onClose(false)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition">
              CANCEL
            </button>
            <button 
              onClick={handleSave} 
              disabled={points.length !== 2 || saving || camera.status !== 'active'} 
              className="px-6 py-2 bg-red-600 text-white font-bold rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {saving ? 'SAVING...' : 'SAVE TRIPWIRE'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
