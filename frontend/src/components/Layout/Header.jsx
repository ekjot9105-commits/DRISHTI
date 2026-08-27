/**
 * Header Bar — Top bar with page title, live stats, and system clock
 */
import { useState, useEffect } from 'react';

export default function Header({ title, activeCameras, totalAlerts }) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <header className="header">
      <h1 className="header-title">{title}</h1>

      <div className="header-actions">
        <div className="header-stat">
          <span className="header-stat-label">Active Cameras</span>
          <span className="header-stat-value">{activeCameras}</span>
        </div>

        <div className="header-stat">
          <span className="header-stat-label">Alerts</span>
          <span className="header-stat-value" style={{
            color: totalAlerts > 0 ? 'var(--accent-danger)' : 'var(--text-primary)'
          }}>
            {totalAlerts}
          </span>
        </div>

        <div className="header-stat">
          <span style={{ fontSize: '14px' }}>🕐</span>
          <span className="header-stat-value">{formatTime(currentTime)}</span>
          <span className="header-stat-label">{formatDate(currentTime)}</span>
        </div>
      </div>
    </header>
  );
}
