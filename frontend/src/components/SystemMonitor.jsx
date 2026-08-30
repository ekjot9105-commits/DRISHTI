import React, { useState, useEffect } from 'react';
import { Activity, Server, Cpu, Clock, Camera } from 'lucide-react';
import { API_BASE } from '../services/api';

export default function SystemMonitor() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/system/status`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (err) {
        console.error(err);
      }
    };
    
    fetchStats();
    const interval = setInterval(fetchStats, 2000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return <div className="p-4 text-slate-500 font-bold text-xs animate-pulse">CONNECTING TO SYSTEM MONITOR...</div>;

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400 bg-green-400/10 border-green-400/30';
      case 'idle': return 'text-slate-400 bg-slate-400/10 border-slate-400/30';
      case 'disabled': return 'text-red-400 bg-red-400/10 border-red-400/30';
      default: return 'text-slate-400 bg-slate-400/10 border-slate-400/30';
    }
  };

  return (
    <div className="bg-[#0b101e] border-t border-[#1e293b] p-4 flex flex-col space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Activity className="w-4 h-4 text-cyan-500" />
        <h3 className="font-bold tracking-wider text-sm text-cyan-500 uppercase">System Performance Monitor</h3>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded p-3 flex flex-col justify-between">
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Cpu className="w-3 h-3" />
            <span className="text-[10px] font-bold tracking-wider">HARDWARE</span>
          </div>
          <div className="flex justify-between items-end">
            <div>
              <div className="text-[10px] text-slate-500">CPU</div>
              <div className="font-mono text-lg text-slate-200">{stats.cpu_usage}%</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-500">RAM</div>
              <div className="font-mono text-lg text-slate-200">{stats.memory_usage}%</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded p-3 flex flex-col justify-between">
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Server className="w-3 h-3" />
            <span className="text-[10px] font-bold tracking-wider">THROUGHPUT</span>
          </div>
          <div className="flex justify-between items-end">
            <div>
              <div className="text-[10px] text-slate-500">SOURCE FPS</div>
              <div className="font-mono text-lg text-cyan-400">{stats.source_fps}</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-500">ML FPS</div>
              <div className="font-mono text-lg text-cyan-400">{stats.inference_fps}</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded p-3 flex flex-col justify-between">
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Clock className="w-3 h-3" />
            <span className="text-[10px] font-bold tracking-wider">LATENCY</span>
          </div>
          <div className="flex justify-between items-end">
            <div>
              <div className="text-[10px] text-slate-500">INFERENCE</div>
              <div className="font-mono text-lg text-amber-400">{stats.inference_latency_ms}ms</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-500">PIPELINE</div>
              <div className="font-mono text-lg text-amber-400">{stats.processing_latency_ms}ms</div>
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded p-3 flex flex-col">
          <div className="flex items-center gap-2 text-slate-400 mb-2">
            <Camera className="w-3 h-3" />
            <span className="text-[10px] font-bold tracking-wider">AI SERVICES</span>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-auto">
            {Object.entries(stats.services).map(([key, status]) => (
              <div key={key} className={`border rounded px-1.5 py-0.5 text-[9px] font-bold tracking-wider uppercase text-center ${getStatusColor(status)}`}>
                {key.replace('_', ' ')}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
