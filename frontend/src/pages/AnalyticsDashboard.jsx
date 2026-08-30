import React, { useState, useEffect } from 'react';
import { Activity, Camera, AlertTriangle, Map } from 'lucide-react';
import { getEventStats, getEventHeatmap } from '../services/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar,
  PieChart, Pie, Cell, Legend
} from 'recharts';
import { MapContainer, TileLayer, CircleMarker, Tooltip as LeafletTooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const AnalyticsDashboard = () => {
  const [stats, setStats] = useState({ timeline: [], severity: [], cameras: [] });
  const [heatmap, setHeatmap] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, heatmapData] = await Promise.all([
          getEventStats(),
          getEventHeatmap()
        ]);
        setStats(statsData);
        setHeatmap(heatmapData);
      } catch (err) {
        console.error("Failed to fetch analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const SEVERITY_COLORS = {
    info: '#3b82f6', // blue
    warning: '#eab308', // yellow
    high: '#f97316', // orange
    critical: '#ef4444' // red
  };

  if (loading) {
    return <div className="p-6 text-slate-400">Loading analytics...</div>;
  }

  return (
    <div className="p-6 h-full flex flex-col space-y-6 overflow-y-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-wider text-cyan-500 flex items-center gap-3">
          <Activity className="w-6 h-6" />
          ANALYTICS DASHBOARD
        </h1>
        <p className="text-slate-400 mt-1 text-sm tracking-widest uppercase">
          Historical Patterns & Geospatial Heatmaps
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Timeline Chart */}
        <div className="bg-[#0b101e] border border-[#1e293b] p-6 rounded-lg shadow-lg">
          <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-500" />
            Detection Volume (Last 24h)
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.timeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis 
                  dataKey="time" 
                  stroke="#64748b" 
                  tickFormatter={(val) => val.split(' ')[1]} 
                  tick={{ fontSize: 12 }} 
                />
                <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#e2e8f0' }}
                />
                <Line type="monotone" dataKey="count" stroke="#06b6d4" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Severity Pie Chart */}
        <div className="bg-[#0b101e] border border-[#1e293b] p-6 rounded-lg shadow-lg">
          <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            Incident Severity Breakdown
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.severity}
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {stats.severity.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name.toLowerCase()] || '#94a3b8'} />
                  ))}
                </Pie>
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#e2e8f0' }}
                />
                <Legend formatter={(value) => <span className="text-slate-300 capitalize">{value}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Camera Activity Bar Chart */}
        <div className="bg-[#0b101e] border border-[#1e293b] p-6 rounded-lg shadow-lg">
          <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Camera className="w-5 h-5 text-indigo-500" />
            Activity by Camera Zone
          </h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats.cameras}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 12 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#e2e8f0' }}
                  cursor={{ fill: '#1e293b' }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Geospatial Heatmap */}
        <div className="bg-[#0b101e] border border-[#1e293b] p-6 rounded-lg shadow-lg">
          <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Map className="w-5 h-5 text-emerald-500" />
            Geospatial Activity Heatmap
          </h2>
          <div className="h-64 rounded overflow-hidden border border-[#1e293b]">
            <MapContainer 
              center={[28.6139, 77.2090]} // Default to New Delhi or adjust
              zoom={12} 
              style={{ height: '100%', width: '100%', background: '#0b101e' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {heatmap.map((point, idx) => (
                <CircleMarker
                  key={idx}
                  center={[point.lat, point.lng]}
                  pathOptions={{ 
                    color: point.intensity > 50 ? '#ef4444' : '#f59e0b',
                    fillColor: point.intensity > 50 ? '#ef4444' : '#f59e0b',
                    fillOpacity: 0.6 
                  }}
                  radius={Math.max(10, Math.min(point.intensity, 30))}
                >
                  <LeafletTooltip>
                    <span className="font-semibold text-slate-800">{point.name}</span><br/>
                    Detections: {point.intensity}
                  </LeafletTooltip>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        </div>

      </div>
    </div>
  );
};

export default AnalyticsDashboard;
