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
import { fetchCameras, createAlertWebSocket } from './services/api';

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
  const [humanCount, setHumanCount] = useState(0);
  const [vehicleCount, setVehicleCount] = useState(0);

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

  // Connect to Alert WebSocket
  useEffect(() => {
    let ws;
    let reconnectTimer;
    
    const connect = () => {
      ws = createAlertWebSocket((alert) => {
        setAlerts(prev => {
          // Prevent duplicate keys if backend sends multiple alerts within the same second
          if (prev.some(a => a.id === alert.id)) return prev;
          return [alert, ...prev].slice(0, 50);
        });
        
        // Update KPI stats
        if (alert.detail && alert.detail.includes('person')) {
          setHumanCount(prev => prev + 1);
        } else if (alert.detail && alert.detail.includes('vehicle')) {
          setVehicleCount(prev => prev + 1);
        }
      });
      
      ws.onclose = () => {
        reconnectTimer = setTimeout(connect, 3000);
      };
    };
    
    connect();
    
    return () => {
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, []);

  const activeCameraCount = cameras.filter((c) => c.status === 'active').length;

  // Render the active page
  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return (
          <Dashboard
            cameras={cameras}
            alerts={alerts}
            humanCount={humanCount}
            vehicleCount={vehicleCount}
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
    <div className="flex h-screen w-full overflow-hidden bg-surface">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />

      <div className="flex flex-col flex-1 pl-20 pt-16 transition-all duration-300 w-full h-full relative">
        <Header
          title={PAGE_TITLES[activePage] || 'IBVAP COMMAND'}
          activeCameras={activeCameraCount}
          totalAlerts={alerts.length}
        />

        <div className="flex-1 overflow-auto bg-surface w-full h-full relative">
          {renderPage()}
        </div>
      </div>
    </div>
  );
}
