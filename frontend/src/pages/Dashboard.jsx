/**
 * Dashboard — Main Command Center view with camera grid, stats, and alert panel.
 */
import CameraGrid from '../components/CameraGrid/CameraGrid';
import AlertPanel from '../components/AlertPanel/AlertPanel';

export default function Dashboard({ cameras, alerts, onNavigate }) {
  const activeCameras = cameras.filter((c) => c.status === 'active').length;

  return (
    <div className="dashboard-layout">
      {/* Main content area */}
      <div className="dashboard-main">
        {/* Quick stats bar */}
        <div className="dashboard-stats-bar">
          <div className="stat-card">
            <div className="stat-card-icon blue">📹</div>
            <div className="stat-card-info">
              <div className="stat-card-value">{activeCameras}</div>
              <div className="stat-card-label">Active Cameras</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon green">👤</div>
            <div className="stat-card-info">
              <div className="stat-card-value">0</div>
              <div className="stat-card-label">Humans Detected</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon orange">🚗</div>
            <div className="stat-card-info">
              <div className="stat-card-value">0</div>
              <div className="stat-card-label">Vehicles Detected</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon red">⚠️</div>
            <div className="stat-card-info">
              <div className="stat-card-value">{alerts.length}</div>
              <div className="stat-card-label">Alerts Today</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-card-icon purple">🛡️</div>
            <div className="stat-card-info">
              <div className="stat-card-value">{cameras.length}</div>
              <div className="stat-card-label">Total Cameras</div>
            </div>
          </div>
        </div>

        {/* Camera grid */}
        <CameraGrid cameras={cameras} />
      </div>

      {/* Alert panel on the right */}
      <AlertPanel alerts={alerts} />
    </div>
  );
}
