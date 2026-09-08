/**
 * IBVAP API Service
 * Central API client for communicating with the FastAPI backend.
 */

// The backend always runs on :8000 of whatever host served this page, so a
// phone opening the LAN URL talks to the LAN backend rather than its own
// localhost. Override with VITE_API_HOST when the backend lives elsewhere.
const API_HOST =
  import.meta.env?.VITE_API_HOST ||
  `${window.location.hostname || 'localhost'}:8000`;

export const API_BASE = `http://${API_HOST}`;
const WS_BASE = `ws://${API_HOST}`;

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

// ---- Settings ----

export async function fetchSettings() {
  return request('/api/settings/');
}

/** Merge-patch the shared settings store (settings.json on the backend). */
export async function updateSettings(patch) {
  return request('/api/settings/', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  });
}

// ---- Demo mode / phone camera / QR ----

export async function fetchDemoVideos() {
  return request('/api/cameras/demo/list');
}

export async function launchDemoVideo(filename) {
  return request(`/api/cameras/demo/${encodeURIComponent(filename)}/launch`, { method: 'POST' });
}

export async function registerPhoneCamera(name = 'Phone Camera', location = 'Mobile Unit') {
  const formData = new FormData();
  formData.append('name', name);
  formData.append('location', location);
  const response = await fetch(`${API_BASE}/api/cameras/phone/register`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchLanUrl(path = '/phone', port = window.location.port || 5173) {
  return request(`/api/system/lan-url?path=${encodeURIComponent(path)}&port=${port}`);
}

export function qrImageUrl(data) {
  return `${API_BASE}/api/system/qr?data=${encodeURIComponent(data)}`;
}

/** Open the frame-push socket used by the phone camera page. */
export function createPushWebSocket(cameraId) {
  const ws = new WebSocket(`${WS_BASE}/ws/cameras/${cameraId}/push`);
  ws.binaryType = 'arraybuffer';
  return ws;
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

export { WS_BASE };


export const getBlockchainStatus = async (eventId) => {
  const response = await fetch(`${API_BASE}/api/events/${eventId}/blockchain`);
  if (!response.ok) throw new Error('Failed to fetch blockchain status');
  return await response.json();
};
