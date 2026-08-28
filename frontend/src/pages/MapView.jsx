import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { fetchCameras } from '../services/api';
import { Map as MapIcon } from 'lucide-react';

// Fix Leaflet marker icons not showing up due to webpack issues
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom red icon for alert state
const alertIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Default blue icon
const defaultIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

// Gray icon for inactive
const inactiveIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

export default function MapView() {
  const [cameras, setCameras] = useState([]);

  useEffect(() => {
    fetchCameras().then(data => {
      // Fake coordinates if they don't have them in the DB yet, for demo purposes
      const enriched = data.map((cam, i) => ({
        ...cam,
        lat: cam.latitude || (28.6139 + (Math.random() * 0.05 - 0.025)),
        lng: cam.longitude || (77.2090 + (Math.random() * 0.05 - 0.025)),
        isAlerting: Math.random() > 0.8 // Random alert state for demo
      }));
      setCameras(enriched);
    });
  }, []);

  return (
    <div className="h-full flex flex-col relative z-0">
      <div className="absolute top-6 left-6 z-[400] pointer-events-none">
        <h1 className="text-2xl font-bold tracking-wider text-cyan-500 flex items-center gap-3 drop-shadow-lg">
          <MapIcon className="w-6 h-6" />
          GEOSPATIAL VIEW
        </h1>
        <p className="text-slate-200 mt-1 text-sm tracking-widest uppercase drop-shadow-md font-bold">
          Real-time physical asset tracking
        </p>
      </div>

      <div className="flex-1 w-full bg-[#0b101e]">
        <MapContainer center={[28.6139, 77.2090]} zoom={13} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          
          {cameras.map(camera => (
            <Marker 
              key={camera.id} 
              position={[camera.lat, camera.lng]}
              icon={camera.status === 'active' ? (camera.isAlerting ? alertIcon : defaultIcon) : inactiveIcon}
            >
              <Popup className="custom-popup">
                <div className="font-sans">
                  <h3 className="font-bold text-sm tracking-wider uppercase mb-1">{camera.name}</h3>
                  <div className="text-xs text-slate-500 mb-2">ID: {camera.id} | {camera.status}</div>
                  <div className="text-xs font-mono bg-slate-100 p-1 rounded">
                    {camera.lat.toFixed(4)}, {camera.lng.toFixed(4)}
                  </div>
                  {camera.isAlerting && (
                    <div className="mt-2 text-xs font-bold text-red-600 bg-red-100 px-2 py-1 rounded">
                      ⚠️ ACTIVE ALERT AT LOCATION
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
      
      {/* Custom styles to force Leaflet popups to look decent */}
      <style>{`
        .leaflet-popup-content-wrapper {
          border-radius: 4px;
        }
        .leaflet-popup-content {
          margin: 12px;
        }
        .leaflet-container {
          background-color: #0b101e !important;
        }
      `}</style>
    </div>
  );
}
