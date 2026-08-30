import React, { useState, useEffect, useRef } from 'react';
import { WS_BASE } from '../services/api';

export default function TripwireModal({ camera, onClose }) {
  const [lines, setLines] = useState([]); // Array of arrays: [ [{x,y}, {x,y}], ... ]
  const [currentLine, setCurrentLine] = useState([]); // Currently drawing line (0 or 1 points)
  const [saving, setSaving] = useState(false);
  const canvasRef = useRef(null);
  const imgRef = useRef(null);
  
  useEffect(() => {
    if (camera.tripwire_line) {
      try {
        const parsed = JSON.parse(camera.tripwire_line);
        // Check if it's the old single-line format [p1, p2] or new multi-line format [ [p1, p2], ... ]
        if (parsed.length > 0) {
          if (Array.isArray(parsed[0])) {
            setLines(parsed); // New format
          } else if (parsed.length === 2) {
            setLines([parsed]); // Old format migrated
          }
        }
      } catch (e) { }
    }
  }, [camera]);

  useEffect(() => {
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
  }, [lines, currentLine]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw saved lines
    lines.forEach(line => {
      if (line.length === 2) {
        ctx.beginPath();
        ctx.arc(line[0].x * canvas.width, line[0].y * canvas.height, 5, 0, 2 * Math.PI);
        ctx.arc(line[1].x * canvas.width, line[1].y * canvas.height, 5, 0, 2 * Math.PI);
        ctx.fillStyle = 'red';
        ctx.fill();
        
        ctx.beginPath();
        ctx.moveTo(line[0].x * canvas.width, line[0].y * canvas.height);
        ctx.lineTo(line[1].x * canvas.width, line[1].y * canvas.height);
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 3;
        ctx.stroke();
      }
    });

    // Draw line currently being drawn
    if (currentLine.length === 1) {
      ctx.beginPath();
      ctx.arc(currentLine[0].x * canvas.width, currentLine[0].y * canvas.height, 5, 0, 2 * Math.PI);
      ctx.fillStyle = 'cyan';
      ctx.fill();
    }
  };

  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    
    if (currentLine.length === 0) {
      // First click
      setCurrentLine([{x, y}]);
    } else if (currentLine.length === 1) {
      // Second click finishes the line
      setLines([...lines, [currentLine[0], {x, y}]]);
      setCurrentLine([]);
    }
  };

  const handleUndo = () => {
    if (currentLine.length === 1) {
      setCurrentLine([]);
    } else if (lines.length > 0) {
      setLines(lines.slice(0, -1));
    }
  };

  const handleClear = async () => {
    setLines([]);
    setCurrentLine([]);
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

  const handleSave = async () => {
    setSaving(true);
    try {
      const { API_BASE } = await import('../services/api');
      // Save all fully formed lines
      await fetch(`${API_BASE}/api/cameras/${camera.id}/tripwire`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tripwire_line: JSON.stringify(lines) })
      });
      onClose(true); // Tell parent to reload
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
            DRAW VIRTUAL TRIPWIRES - {camera.name}
          </h3>
          <button className="text-slate-400 hover:text-white" onClick={() => onClose(false)}>
            ✕
          </button>
        </div>
        
        <div className="p-4 flex-1 flex flex-col bg-black">
          <p className="text-sm text-slate-400 mb-2 uppercase tracking-widest text-center">
            Click points on the video to define multiple intrusion perimeter lines.
          </p>
          <p className="text-xs text-amber-500 mb-4 uppercase tracking-widest text-center font-bold bg-amber-500/10 py-1 rounded w-fit mx-auto px-4 border border-amber-500/30">
            ⚠️ WARNING: TRIPWIRES REQUIRE A STATIONARY CAMERA. DO NOT USE ON PTZ OR MOVING CAMERAS.
          </p>
          
          <div className="relative mx-auto border border-[#1e293b] w-full max-w-3xl aspect-video bg-[#1e293b]/20">
            {camera.status === 'active' ? (
              <>
                <img ref={imgRef} className="absolute inset-0 w-full h-full" style={{ objectFit: 'fill' }} alt="Live Feed" />
                <canvas 
                  ref={canvasRef} 
                  className="absolute inset-0 w-full h-full cursor-crosshair z-10"
                  style={{ objectFit: 'fill' }}
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
          <div className="flex gap-2">
            <button onClick={handleUndo} disabled={lines.length === 0 && currentLine.length === 0} className="px-4 py-2 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 disabled:opacity-50 transition">
              UNDO
            </button>
            <button onClick={handleClear} className="px-4 py-2 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition">
              CLEAR ALL
            </button>
          </div>
          <div className="flex gap-3">
            <button onClick={() => onClose(false)} className="px-4 py-2 bg-slate-800 text-slate-300 rounded hover:bg-slate-700 transition">
              CANCEL
            </button>
            <button 
              onClick={handleSave} 
              disabled={saving || camera.status !== 'active'} 
              className="px-6 py-2 bg-red-600 text-white font-bold rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {saving ? 'SAVING...' : `SAVE ${lines.length} TRIPWIRES`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
