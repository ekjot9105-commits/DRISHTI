/**
 * AlertPanel — Live alerts sidebar showing real-time detection notifications.
 * Placeholder for Phase 1 — will be connected to WebSocket alerts in Phase 2.
 */
import { useState } from 'react';

// Sample placeholder alerts for visual design (replaced by real alerts in Phase 2)
const sampleAlerts = [
  {
    id: 1,
    type: 'info',
    severity: 'info',
    title: 'System Online',
    detail: 'IBVAP platform initialized successfully',
    time: 'Just now',
    icon: '✅',
  },
];

export default function AlertPanel({ alerts = [] }) {
  const displayAlerts = alerts.length > 0 ? alerts : sampleAlerts;

  return (
    <aside className="alert-panel">
      {/* Header */}
      <div className="alert-panel-header">
        <span className="alert-panel-title">Live Alerts</span>
        {displayAlerts.length > 0 && (
          <span className="alert-panel-count">{displayAlerts.length}</span>
        )}
      </div>

      {/* Alert List */}
      <div className="alert-panel-list">
        {displayAlerts.map((alert) => (
          <div key={alert.id} className={`alert-item ${alert.severity}`}>
            <span className="alert-item-icon">{alert.icon}</span>
            <div className="alert-item-content">
              <div className="alert-item-title">{alert.title}</div>
              <div className="alert-item-detail">{alert.detail}</div>
            </div>
            <span className="alert-item-time">{alert.time}</span>
          </div>
        ))}

        {displayAlerts.length === 0 && (
          <div className="empty-state" style={{ padding: 'var(--space-xl)' }}>
            <div style={{ fontSize: '32px', opacity: 0.3 }}>🔔</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
              No alerts — All clear
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
