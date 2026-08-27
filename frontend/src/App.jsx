/**
 * IBVAP — Intelligent Border Video Analytics Platform
 * Main Application Component
 *
 * Manages navigation, camera state, and renders the appropriate page.
 */
import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';
import Dashboard from './pages/Dashboard';
import CameraManagement from './pages/CameraManagement';
import PlaceholderPage from './pages/PlaceholderPage';
import { fetchCameras } from './services/api';

const PAGE_TITLES = {
  dashboard: 'Command Center',
  cameras: 'Camera Management',
  alerts: 'Alert Center',
  analytics: 'Analytics Dashboard',
  watchlist: 'Watchlist Management',
  map: 'Geospatial Map View',
  evidence: 'Evidence Vault',
  settings: 'System Settings',
};

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [cameras, setCameras] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [backendOnline, setBackendOnline] = useState(false);

  // Fetch cameras from backend
  const loadCameras = useCallback(async () => {
    try {
      const data = await fetchCameras();
      setCameras(data);
      setBackendOnline(true);
    } catch (err) {
      console.warn('Backend not reachable:', err.message);
      setBackendOnline(false);
    }
  }, []);

  // Load cameras on mount and poll every 5 seconds
  useEffect(() => {
    loadCameras();
    const interval = setInterval(loadCameras, 5000);
    return () => clearInterval(interval);
  }, [loadCameras]);

  const activeCameraCount = cameras.filter((c) => c.status === 'active').length;

  // Render the active page
  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return (
          <Dashboard
            cameras={cameras}
            alerts={alerts}
            onNavigate={setActivePage}
          />
        );
      case 'cameras':
        return (
          <CameraManagement
            cameras={cameras}
            onCamerasChange={loadCameras}
          />
        );
      case 'alerts':
        return (
          <PlaceholderPage
            title="Alert Center"
            description="Real-time alert management — Coming in Phase 2"
            icon="🔔"
          />
        );
      case 'analytics':
        return (
          <PlaceholderPage
            title="Analytics Dashboard"
            description="Detection charts and heatmaps — Coming in Phase 4"
            icon="📊"
          />
        );
      case 'watchlist':
        return (
          <PlaceholderPage
            title="Watchlist Management"
            description="Face and vehicle plate watchlists — Coming in Phase 3"
            icon="👤"
          />
        );
      case 'map':
        return (
          <PlaceholderPage
            title="Geospatial Map View"
            description="Camera locations and events on map — Coming in Phase 5"
            icon="🗺️"
          />
        );
      case 'evidence':
        return (
          <PlaceholderPage
            title="Evidence Vault"
            description="Blockchain-verified video evidence — Coming in Phase 5"
            icon="🔒"
          />
        );
      case 'settings':
        return (
          <PlaceholderPage
            title="System Settings"
            description="User management and configuration — Coming in Phase 5"
            icon="⚙️"
          />
        );
      default:
        return <Dashboard cameras={cameras} alerts={alerts} onNavigate={setActivePage} />;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />

      <div className="main-area">
        <Header
          title={PAGE_TITLES[activePage] || 'IBVAP'}
          activeCameras={activeCameraCount}
          totalAlerts={alerts.length}
        />

        {!backendOnline && (
          <div style={{
            padding: '8px 24px',
            background: 'rgba(245, 158, 11, 0.1)',
            borderBottom: '1px solid rgba(245, 158, 11, 0.3)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '12px',
            color: 'var(--accent-warning)',
          }}>
            ⚠️ Backend server not connected. Start it with: <code style={{
              fontFamily: 'var(--font-mono)',
              background: 'var(--bg-tertiary)',
              padding: '2px 8px',
              borderRadius: '4px',
            }}>cd backend && uvicorn app.main:app --reload</code>
          </div>
        )}

        {renderPage()}
      </div>
    </div>
  );
}
