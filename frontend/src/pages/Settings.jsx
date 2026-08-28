import React, { useState, useEffect } from 'react';
import { API_BASE } from '../services/api';

export default function Settings() {
  const [settings, setSettings] = useState({
    confidence_threshold: 0.35,
    intrusion_cooldown: 10.0,
    dwelling_time: 10.0,
    night_mode: false
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
      [name]: type === 'checkbox' ? checked : parseFloat(value)
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
    <div className="p-6 h-full flex flex-col space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-wider text-cyan-500">SYSTEM SETTINGS</h1>
        <p className="text-slate-400 mt-1 text-sm tracking-widest uppercase">
          Global Machine Learning & Application Configuration
        </p>
      </div>

      <div className="bg-[#0b101e] border border-[#1e293b] rounded-lg shadow-lg p-6">
        <form onSubmit={handleSave} className="space-y-6">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 border-b border-[#1e293b] pb-2">ML Inference Thresholds</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">CONFIDENCE THRESHOLD (0.0 - 1.0)</label>
                <input 
                  type="number" 
                  step="0.05"
                  min="0.1"
                  max="0.95"
                  name="confidence_threshold"
                  value={settings.confidence_threshold}
                  onChange={handleChange}
                  className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500">Minimum confidence to register an object.</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 border-b border-[#1e293b] pb-2">Alert Cooldowns</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">INTRUSION COOLDOWN (SEC)</label>
                <input 
                  type="number" 
                  name="intrusion_cooldown"
                  value={settings.intrusion_cooldown}
                  onChange={handleChange}
                  className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500">Minimum time between tripwire alerts for the same object.</span>
              </div>

              <div className="flex flex-col space-y-2">
                <label className="text-xs font-bold text-slate-400 tracking-wider">DWELLING TIME (SEC)</label>
                <input 
                  type="number" 
                  name="dwelling_time"
                  value={settings.dwelling_time}
                  onChange={handleChange}
                  className="bg-slate-900 border border-slate-700 text-slate-200 px-4 py-2 rounded focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500">How long an object must be present to trigger a dwelling alert.</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-200 border-b border-[#1e293b] pb-2">Image Processing</h3>
            
            <label className="flex items-center space-x-3 cursor-pointer">
              <input 
                type="checkbox" 
                name="night_mode"
                checked={settings.night_mode}
                onChange={handleChange}
                className="w-5 h-5 accent-cyan-500"
              />
              <div>
                <span className="text-sm font-bold text-slate-300 tracking-wider">ENABLE NIGHT MODE ENHANCEMENT (CLAHE)</span>
                <p className="text-[10px] text-slate-500 mt-1">Applies Contrast Limited Adaptive Histogram Equalization to brighten dark feeds before YOLO tracking.</p>
              </div>
            </label>
          </div>

          <div className="pt-4 border-t border-[#1e293b] flex items-center justify-between">
            {success ? <span className="text-green-500 text-sm font-bold tracking-wider">SETTINGS SAVED!</span> : <span />}
            <button 
              type="submit" 
              disabled={saving}
              className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded font-bold tracking-wider transition-colors disabled:opacity-50"
            >
              {saving ? 'SAVING...' : 'SAVE CONFIGURATION'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
