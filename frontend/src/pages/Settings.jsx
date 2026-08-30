import React, { useState, useEffect } from 'react';
import { API_BASE } from '../services/api';

export default function Settings() {
  const [settings, setSettings] = useState({
    confidence_threshold: 0.35,
    intrusion_cooldown: 10.0,
    dwelling_time: 10.0,
    night_mode: false,
    fleeing_threshold: 300.0,
    fleeing_duration: 1.5,
    crowd_count: 3,
    crowd_density: 150.0,
    crowd_duration: 60.0,
    webhook_url: ""
  });
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/api/settings/`)
      .then(res => res.json())
      .then(data => setSettings(data))
      .catch(err => console.error(err));
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'text' ? value : parseFloat(value))
    }));
    setSuccess(false);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await fetch(`${API_BASE}/api/settings/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 h-full flex flex-col space-y-6 max-w-4xl mx-auto overflow-y-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-wider text-cyan-500">SYSTEM SETTINGS</h1>
        <p className="text-slate-400 mt-1 text-sm tracking-widest uppercase">
          Global Machine Learning & Application Configuration
        </p>
      </div>

      <div className="bg-[#0b101e] border border-[#1e293b] rounded-lg shadow-lg p-6 mb-10">
        <form onSubmit={handleSave} className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 border-b border-[#1e293b] pb-2">ML Inference Thresholds</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">CONFIDENCE THRESHOLD (0.0 - 1.0)</label>
                <input type="number" step="0.05" name="confidence_threshold" value={settings.confidence_threshold} onChange={handleChange} className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500" />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 border-b border-[#1e293b] pb-2">Behavioral Analytics: Fleeing/Running</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">SPEED THRESHOLD (PX/SEC)</label>
                <input type="number" name="fleeing_threshold" value={settings.fleeing_threshold} onChange={handleChange} className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500" />
              </div>
              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">MIN DURATION (SEC)</label>
                <input type="number" step="0.5" name="fleeing_duration" value={settings.fleeing_duration} onChange={handleChange} className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500" />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 border-b border-[#1e293b] pb-2">Behavioral Analytics: Crowd Gathering</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">MIN PEOPLE COUNT</label>
                <input type="number" name="crowd_count" value={settings.crowd_count} onChange={handleChange} className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500" />
              </div>
              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">DENSITY (PX RADIUS)</label>
                <input type="number" name="crowd_density" value={settings.crowd_density} onChange={handleChange} className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500" />
              </div>
              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">MIN DURATION (SEC)</label>
                <input type="number" name="crowd_duration" value={settings.crowd_duration} onChange={handleChange} className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500" />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 border-b border-[#1e293b] pb-2">Command & Control Integration</h3>
            <div className="flex flex-col space-y-2">
              <label className="text-xs font-bold text-slate-400 tracking-wider">WEBHOOK URL (ASYNC DISPATCH)</label>
              <input type="text" name="webhook_url" value={settings.webhook_url} onChange={handleChange} placeholder="https://ssb-hq.gov.in/api/alerts" className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500" />
            </div>
          </div>

          <div className="pt-4 border-t border-[#1e293b] flex items-center justify-between">
            {success ? <span className="text-green-500 text-sm font-bold tracking-wider">SETTINGS SAVED!</span> : <span />}
            <button type="submit" disabled={saving} className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded font-bold tracking-wider transition-colors disabled:opacity-50">
              {saving ? 'SAVING...' : 'SAVE CONFIGURATION'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
