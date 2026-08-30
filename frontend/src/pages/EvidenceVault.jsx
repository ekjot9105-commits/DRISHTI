import React, { useState, useEffect } from 'react';
import { getEvents, API_BASE } from '../services/api';
import { Lock, Download, FileText } from 'lucide-react';

export default function EvidenceVault() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      // Get a large batch of alerts, we will filter for those with evidence on client side
      const data = await getEvents(0, 500, null, null, null);
      setEvents(data.filter(e => e.thumbnail_path));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = (eventId) => {
    window.location.href = `${API_BASE}/api/events/${eventId}/evidence/download`;
  };

  const downloadReport = (eventId) => {
    window.location.href = `${API_BASE}/api/reports/${eventId}/download`;
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-cyan-500 flex items-center gap-3">
            <Lock className="w-6 h-6" />
            EVIDENCE VAULT
          </h1>
          <p className="text-slate-400 mt-1 text-sm tracking-widest uppercase">
            Secure visual evidence gallery from intrusion events
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-auto bg-[#0b101e] border border-[#1e293b] rounded-lg p-6">
        {loading ? (
          <div className="text-center text-slate-500 mt-20 font-bold tracking-widest">LOADING VAULT...</div>
        ) : events.length === 0 ? (
          <div className="text-center text-slate-500 mt-20 font-bold tracking-widest">NO EVIDENCE FOUND</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {events.map(event => (
              <div key={event.id} className="bg-[#151e32] border border-[#1e293b] rounded-lg overflow-hidden group">
                <div className="relative aspect-video bg-black flex items-center justify-center">
                  <img 
                    src={`${API_BASE}${event.thumbnail_path}`} 
                    alt={event.title}
                    className="w-full h-full object-contain"
                  />
                  <div className="absolute inset-0 bg-cyan-900/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2">
                    <button 
                      onClick={() => downloadImage(event.id)}
                      className="bg-slate-800 border border-slate-600 hover:bg-slate-700 text-white px-3 py-1.5 rounded text-xs font-bold tracking-wider flex items-center gap-2 transform translate-y-4 group-hover:translate-y-0 transition-transform"
                    >
                      <Download className="w-3 h-3" /> JPG EVIDENCE
                    </button>
                    <button 
                      onClick={() => downloadReport(event.id)}
                      className="bg-cyan-500 hover:bg-cyan-400 text-black px-3 py-1.5 rounded text-xs font-bold tracking-wider flex items-center gap-2 transform translate-y-4 group-hover:translate-y-0 transition-transform delay-75"
                    >
                      <FileText className="w-3 h-3" /> PDF REPORT
                    </button>
                  </div>
                </div>
                <div className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-bold text-red-400 uppercase tracking-wider">{event.event_type.replace('_', ' ')}</span>
                    <span className="text-[10px] text-slate-500">{new Date(event.created_at).toLocaleString()}</span>
                  </div>
                  <h3 className="text-slate-200 font-medium text-sm truncate">{event.title}</h3>
                  <p className="text-slate-500 text-xs mt-1 truncate">Camera {event.camera_id}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
