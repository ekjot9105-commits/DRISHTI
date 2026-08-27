/**
 * Sidebar Navigation — Command Center left panel
 */
import { useState } from 'react';

const navItems = [
  { id: 'dashboard', label: 'Command Center', icon: '🖥️', section: 'MONITORING' },
  { id: 'cameras', label: 'Camera Management', icon: '📹', section: 'MONITORING' },
  { id: 'alerts', label: 'Alert Center', icon: '🔔', section: 'MONITORING' },
  { id: 'analytics', label: 'Analytics', icon: '📊', section: 'INTELLIGENCE' },
  { id: 'watchlist', label: 'Watchlist', icon: '👤', section: 'INTELLIGENCE' },
  { id: 'map', label: 'Map View', icon: '🗺️', section: 'INTELLIGENCE' },
  { id: 'evidence', label: 'Evidence Vault', icon: '🔒', section: 'SECURITY' },
  { id: 'settings', label: 'Settings', icon: '⚙️', section: 'SYSTEM' },
];

export default function Sidebar({ activePage, onNavigate }) {
  const sections = [...new Set(navItems.map((item) => item.section))];

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">IV</div>
        <div className="sidebar-brand-text">
          <span className="sidebar-brand-name">IBVAP</span>
          <span className="sidebar-brand-sub">Command Center</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {sections.map((section) => (
          <div key={section}>
            <div className="sidebar-section-label">{section}</div>
            {navItems
              .filter((item) => item.section === section)
              .map((item) => (
                <button
                  key={item.id}
                  className={`sidebar-item ${activePage === item.id ? 'active' : ''}`}
                  onClick={() => onNavigate(item.id)}
                >
                  <span className="sidebar-item-icon">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              ))}
          </div>
        ))}
      </nav>

      {/* Status footer */}
      <div className="sidebar-status">
        <span className="sidebar-status-dot online"></span>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>System Online</span>
      </div>
    </aside>
  );
}
