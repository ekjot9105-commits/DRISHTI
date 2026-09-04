/**
 * IBVAP API Service
 * Central API client for communicating with the FastAPI backend.
 */

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

/**
 * Generic fetch wrapper with error handling.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// ---- Camera API ----

export async function fetchCameras() {
  return request('/api/cameras/');
}

export async function addCamera(formData) {
  const response = await fetch(`${API_BASE}/api/cameras/`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function startCamera(cameraId) {
  return request(`/api/cameras/${cameraId}/start`, { method: 'POST' });
}

export async function stopCamera(cameraId) {
  return request(`/api/cameras/${cameraId}/stop`, { method: 'POST' });
}

export async function deleteCamera(cameraId) {
  return request(`/api/cameras/${cameraId}`, { method: 'DELETE' });
}

export async function fetchStreamStatus() {
  return request('/api/cameras/streams/status');
}

export async function fetchHealth() {
  return request('/api/health');
}

// ---- WebSocket Connections ----

export function createCameraWebSocket(cameraId, onMessage, onError) {
  const ws = new WebSocket(`${WS_BASE}/ws/camera/${cameraId}`);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('WebSocket parse error:', e);
    }
  };

  ws.onerror = (event) => {
    console.error(`Camera ${cameraId} WebSocket error:`, event);
    if (onError) onError(event);
  };

  ws.onclose = () => {
    console.log(`Camera ${cameraId} WebSocket closed`);
  };

  return ws;
}

export function createAlertWebSocket(onAlert) {
  const ws = new WebSocket(`${WS_BASE}/ws/alerts`);

  ws.onmessage = (event) => {
    try {
      const alert = JSON.parse(event.data);
      onAlert(alert);
    } catch (e) {
      console.error('Alert WebSocket parse error:', e);
    }
  };

  ws.onerror = (event) => {
    console.error('Alert WebSocket error:', event);
  };

  return ws;
}

// ---- Watchlist API ----

export async function getFaces() {
  return request('/api/watchlist/faces');
}

export async function addFace(name, description, imageFile, isAuthorized = false) {
  const formData = new FormData();
  formData.append('name', name);
  formData.append('description', description);
  formData.append('image', imageFile);
  formData.append('is_authorized', isAuthorized);
  
  const response = await fetch(`${API_BASE}/api/watchlist/faces`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function deleteFace(id) {
  return request(`/api/watchlist/faces/${id}`, { method: 'DELETE' });
}

export async function getPlates() {
  return request('/api/watchlist/plates');
}

export async function addPlate(plateNumber, vehicleDesc, ownerName) {
  const formData = new FormData();
  formData.append('plate_number', plateNumber);
  formData.append('vehicle_description', vehicleDesc);
  formData.append('owner_name', ownerName);
  // Setting a default critical level as designed in Phase 3
  formData.append('alert_level', 'critical');
  
  const response = await fetch(`${API_BASE}/api/watchlist/plates`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function deletePlate(id) {
  return request(`/api/watchlist/plates/${id}`, { method: 'DELETE' });
}

// ---- Events API ----

export async function getEvents(skip = 0, limit = 100, camera_id = null, severity = null, status = null) {
  let url = `/api/events/?skip=${skip}&limit=${limit}`;
  if (camera_id) url += `&camera_id=${camera_id}`;
  if (severity) url += `&severity=${severity}`;
  if (status) url += `&status=${status}`;
  return request(url);
}

export async function updateEventStatus(eventId, status) {
  return request(`/api/events/${eventId}/status?status=${status}`, { method: 'PATCH' });
}

export async function getEventStats() {
  return request('/api/events/stats');
}

export async function getEventHeatmap() {
  return request('/api/events/heatmap');
}

export { API_BASE, WS_BASE };


export const getBlockchainStatus = async (eventId) => {
  const response = await fetch(`${API_BASE}/api/events/${eventId}/blockchain`);
  if (!response.ok) throw new Error('Failed to fetch blockchain status');
  return await response.json();
};
