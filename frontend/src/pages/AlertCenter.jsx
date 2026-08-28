import React, { useState, useEffect } from 'react';
import { ShieldAlert, AlertTriangle, Info, CheckCircle, Archive, Eye, Image as ImageIcon } from 'lucide-react';
import { getEvents, updateEventStatus, API_BASE } from '../services/api';

const AlertCenter = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ severity: '', status: 'new' });
  const [evidenceImage, setEvidenceImage] = useState(null);

  useEffect(() => {
    fetchEvents();
  }, [filter]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await getEvents(0, 100, null, filter.severity || null, filter.status || null);
      setEvents(data);
    } catch (err) {
      console.error("Failed to fetch events:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (id, status) => {
    try {
      await updateEventStatus(id, status);
      fetchEvents();
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return <ShieldAlert className="text-red-500 w-5 h-5" />;
      case 'high': return <AlertTriangle className="text-orange-500 w-5 h-5" />;
      case 'warning': return <AlertTriangle className="text-yellow-500 w-5 h-5" />;
      default: return <Info className="text-blue-500 w-5 h-5" />;
    }
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-cyan-500 flex items-center gap-3">
            <ShieldAlert className="w-6 h-6" />
            ALERT CENTER
          </h1>
          <p className="text-slate-400 mt-1 text-sm tracking-widest uppercase">
            Historical Evidence & Audit Log
          </p>
        </div>
        
        <div className="flex gap-4">
          <select 
            value={filter.status} 
            onChange={e => setFilter({...filter, status: e.target.value})}
            className="bg-slate-900 border border-slate-700 text-slate-300 px-4 py-2 rounded"
          >
            <option value="">All Statuses</option>
            <option value="new">New</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
            <option value="archived">Archived</option>
          </select>
          <select 
            value={filter.severity} 
            onChange={e => setFilter({...filter, severity: e.target.value})}
            className="bg-slate-900 border border-slate-700 text-slate-300 px-4 py-2 rounded"
          >
            <option value="">All Severities</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <div className="bg-[#0b101e] border border-[#1e293b] rounded-lg shadow-lg flex-1 overflow-hidden flex flex-col">
        <div className="overflow-auto p-4 flex-1">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#1e293b] text-slate-400 text-sm tracking-wider">
                <th className="py-4 px-4">TIMESTAMP</th>
                <th className="py-4 px-4">SEVERITY</th>
                <th className="py-4 px-4">CAMERA ID</th>
                <th className="py-4 px-4">EVENT TYPE</th>
                <th className="py-4 px-4">DETAILS</th>
                <th className="py-4 px-4">STATUS</th>
                <th className="py-4 px-4 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {events.length === 0 && !loading && (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-slate-500">
                    No alerts found for the current filters.
                  </td>
                </tr>
              )}
              {events.map((event) => (
                <tr key={event.id} className="border-b border-[#1e293b]/50 hover:bg-[#151e32] transition-colors">
                  <td className="py-3 px-4 text-sm font-mono text-slate-300">
                    {new Date(event.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {getSeverityIcon(event.severity)}
                      <span className="capitalize text-slate-300">{event.severity}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-slate-300">Cam {event.camera_id}</td>
                  <td className="py-3 px-4 text-slate-300 capitalize">{event.event_type.replace('_', ' ')}</td>
                  <td className="py-3 px-4">
                    <div className="text-slate-200 font-medium">{event.title}</div>
                    <div className="text-slate-500 text-sm">{event.detail}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-xs font-semibold uppercase tracking-wider
                      ${event.status === 'new' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : ''}
                      ${event.status === 'acknowledged' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' : ''}
                      ${event.status === 'resolved' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : ''}
                      ${event.status === 'archived' ? 'bg-slate-500/10 text-slate-400 border border-slate-500/20' : ''}
                    `}>
                      {event.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex justify-end gap-2">
                      {event.status === 'new' && (
                        <button 
                          onClick={() => handleStatusUpdate(event.id, 'acknowledged')}
                          className="p-2 bg-yellow-500/10 hover:bg-yellow-500/20 text-yellow-500 rounded border border-yellow-500/20 transition-colors"
                          title="Acknowledge"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                      {['new', 'acknowledged'].includes(event.status) && (
                        <button 
                          onClick={() => handleStatusUpdate(event.id, 'resolved')}
                          className="p-2 bg-green-500/10 hover:bg-green-500/20 text-green-500 rounded border border-green-500/20 transition-colors"
                          title="Resolve"
                        >
                          <CheckCircle className="w-4 h-4" />
                        </button>
                      )}
                      {['resolved', 'acknowledged'].includes(event.status) && (
                        <button 
                          onClick={() => handleStatusUpdate(event.id, 'archived')}
                          className="p-2 bg-slate-700/50 hover:bg-slate-700 text-slate-300 rounded border border-slate-600 transition-colors"
                          title="Archive"
                        >
                          <Archive className="w-4 h-4" />
                        </button>
                      )}
                      {event.thumbnail_path && (
                        <button 
                          onClick={() => setEvidenceImage(`${API_BASE}${event.thumbnail_path}`)}
                          className="p-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-500 rounded border border-blue-500/20 transition-colors"
                          title="View Evidence Snapshot"
                        >
                          <ImageIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {evidenceImage && (
        <div className="fixed inset-0 bg-black/90 z-[100] flex items-center justify-center p-4 backdrop-blur-sm" onClick={() => setEvidenceImage(null)}>
          <div className="relative max-w-5xl w-full" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold tracking-wider text-cyan-500 flex items-center gap-2">
                <ImageIcon className="w-5 h-5" /> EVIDENCE VAULT SNAPSHOT
              </h3>
              <button className="text-slate-400 hover:text-white" onClick={() => setEvidenceImage(null)}>✕</button>
            </div>
            <img src={evidenceImage} className="w-full h-auto rounded border border-[#1e293b]" alt="Event Evidence" />
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertCenter;
