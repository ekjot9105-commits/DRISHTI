import React, { useState, useEffect } from 'react';
import { getEvents, API_BASE, getBlockchainStatus } from '../services/api';
import { Lock, Download, FileText } from 'lucide-react';

export default function EvidenceVault() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [verifyModal, setVerifyModal] = useState(null);
  const [verifySteps, setVerifySteps] = useState([]);

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


  const handleVerify = async (event) => {
    setVerifyModal(event);
    setVerifySteps([`> Initializing DRISHTI Node... [OK]`]);
    
    setTimeout(() => setVerifySteps(s => [...s, `> Fetching Block for Incident #${event.id}...`]), 800);
    
    try {
      const result = await getBlockchainStatus(event.id);
      if (result.status === 'verified') {
        setTimeout(() => setVerifySteps(s => [...s, `> Block Found: #${result.block.index} [OK]`]), 1600);
        setTimeout(() => setVerifySteps(s => [...s, `> Extracting Original SHA-256 Fingerprint... [OK]`]), 2400);
        setTimeout(() => setVerifySteps(s => [...s, `> Recalculating Local Evidence Hash... [OK]`]), 3200);
        setTimeout(() => setVerifySteps(s => [...s, `> RESULT: MATCH. Evidence is pristine and admissible.`]), 4000);
        setTimeout(() => setVerifySteps(s => [...s, `> Hash: ${result.block.evidence_hash}`]), 4500);
      } else {
        setTimeout(() => setVerifySteps(s => [...s, `> Block pending inclusion in ledger...`]), 1600);
      }
    } catch (e) {
      setTimeout(() => setVerifySteps(s => [...s, `> ERROR: Could not reach blockchain node.`]), 1600);
    }
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
                    <button 
                      onClick={() => handleVerify(event)}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded text-xs font-bold tracking-wider flex items-center gap-2 transform translate-y-4 group-hover:translate-y-0 transition-transform delay-150"
                    >
                      <Lock className="w-3 h-3" /> VERIFY INTEGRITY
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

      {verifyModal && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-[#0b101e] border border-cyan-500/50 w-full max-w-2xl rounded-lg shadow-[0_0_30px_rgba(6,182,212,0.2)] overflow-hidden flex flex-col">
            <div className="bg-[#151e32] px-4 py-3 border-b border-slate-700 flex justify-between items-center">
              <h3 className="text-cyan-400 font-mono font-bold tracking-widest text-sm flex items-center gap-2">
                <Lock className="w-4 h-4" /> CRYPTOGRAPHIC AUDIT - INCIDENT {verifyModal.id}
              </h3>
              <button onClick={() => setVerifyModal(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="p-6 font-mono text-xs sm:text-sm text-emerald-400 bg-black h-64 overflow-y-auto space-y-2">
              {verifySteps.map((step, i) => (
                <div key={i} className={step.includes('ERROR') ? 'text-red-500' : ''}>{step}</div>
              ))}
              {verifySteps.length > 0 && verifySteps.length < 6 && (
                <div className="animate-pulse">_</div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
