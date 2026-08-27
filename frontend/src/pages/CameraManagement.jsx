/**
 * CameraManagement — Add, configure, start/stop, and delete camera sources.
 * Supports video file upload and RTSP URL input.
 */
import { useState, useRef } from 'react';
import { addCamera, startCamera, stopCamera, deleteCamera } from '../services/api';

export default function CameraManagement({ cameras, onCamerasChange }) {
  const [showModal, setShowModal] = useState(false);
  const [sourceType, setSourceType] = useState('file');
  const [name, setName] = useState('');
  const [location, setLocation] = useState('');
  const [rtspUrl, setRtspUrl] = useState('');
  const [videoFile, setVideoFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const resetForm = () => {
    setName('');
    setLocation('');
    setRtspUrl('');
    setVideoFile(null);
    setSourceType('file');
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('name', name);
      formData.append('source_type', sourceType);
      formData.append('location', location);

      if (sourceType === 'file') {
        if (!videoFile) {
          setError('Please select a video file');
          setLoading(false);
          return;
        }
        formData.append('video_file', videoFile);
      } else {
        if (!rtspUrl) {
          setError('Please enter an RTSP URL');
          setLoading(false);
          return;
        }
        formData.append('source_url', rtspUrl);
      }

      await addCamera(formData);
      resetForm();
      setShowModal(false);
      onCamerasChange(); // Refresh camera list
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (cameraId) => {
    try {
      await startCamera(cameraId);
      onCamerasChange();
    } catch (err) {
      console.error('Failed to start camera:', err);
    }
  };

  const handleStop = async (cameraId) => {
    try {
      await stopCamera(cameraId);
      onCamerasChange();
    } catch (err) {
      console.error('Failed to stop camera:', err);
    }
  };

  const handleDelete = async (cameraId) => {
    if (!confirm('Are you sure you want to delete this camera?')) return;
    try {
      await deleteCamera(cameraId);
      onCamerasChange();
    } catch (err) {
      console.error('Failed to delete camera:', err);
    }
  };

  return (
    <div className="page-content">
      {/* Page header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Camera Management</h2>
          <p className="page-subtitle">Configure and manage surveillance camera sources</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          + Add Camera
        </button>
      </div>

      {/* Camera cards */}
      {cameras.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📹</div>
          <div className="empty-state-text">No cameras configured</div>
          <p className="empty-state-sub">Add your first camera to start monitoring</p>
          <button
            className="btn btn-primary"
            style={{ marginTop: '16px' }}
            onClick={() => setShowModal(true)}
          >
            + Add Camera
          </button>
        </div>
      ) : (
        <div className="camera-management-grid">
          {cameras.map((camera) => (
            <div key={camera.id} className="camera-card">
              <div className="camera-card-preview">
                <div className="camera-feed-empty">
                  <div style={{ fontSize: '36px', opacity: 0.3 }}>
                    {camera.status === 'active' ? '🟢' : '📹'}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {camera.source_type === 'file' ? 'Video File' : 'RTSP Stream'}
                  </div>
                </div>
              </div>
              <div className="camera-card-body">
                <div className="camera-card-name">{camera.name}</div>
                <div className="camera-card-meta">
                  <span className={`badge ${camera.status === 'active' ? 'badge-success' : 'badge-warning'}`}>
                    {camera.status === 'active' ? '● Active' : '○ Inactive'}
                  </span>
                  {camera.location && (
                    <span style={{ marginLeft: '8px', color: 'var(--text-muted)' }}>
                      📍 {camera.location}
                    </span>
                  )}
                </div>
                <div className="camera-card-actions">
                  {camera.status === 'active' ? (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleStop(camera.id)}
                    >
                      ⏹ Stop
                    </button>
                  ) : (
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => handleStart(camera.id)}
                    >
                      ▶ Start
                    </button>
                  )}
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleDelete(camera.id)}
                  >
                    🗑 Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Camera Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Add Camera Source</h3>
              <button className="modal-close" onClick={() => { setShowModal(false); resetForm(); }}>
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                {error && (
                  <div style={{
                    padding: '8px 12px',
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '8px',
                    color: 'var(--accent-danger)',
                    fontSize: '13px',
                  }}>
                    {error}
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Camera Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g., BOP Alpha Gate Camera"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Location (optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g., North Gate, Sector 7"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Source Type</label>
                  <div className="tabs">
                    <button
                      type="button"
                      className={`tab ${sourceType === 'file' ? 'active' : ''}`}
                      onClick={() => setSourceType('file')}
                    >
                      📂 Video File
                    </button>
                    <button
                      type="button"
                      className={`tab ${sourceType === 'rtsp' ? 'active' : ''}`}
                      onClick={() => setSourceType('rtsp')}
                    >
                      📡 RTSP Camera
                    </button>
                  </div>
                </div>

                {sourceType === 'file' ? (
                  <div className="form-group">
                    <label className="form-label">Video File</label>
                    <div
                      className="file-upload"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <div className="file-upload-icon">📁</div>
                      <div className="file-upload-text">
                        {videoFile ? videoFile.name : 'Click to select video file'}
                      </div>
                      <div className="file-upload-hint">
                        Supported: MP4, AVI, MKV, MOV
                      </div>
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="video/*"
                      style={{ display: 'none' }}
                      onChange={(e) => setVideoFile(e.target.files[0])}
                    />
                  </div>
                ) : (
                  <div className="form-group">
                    <label className="form-label">RTSP URL</label>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="rtsp://username:password@192.168.1.100:554/stream"
                      value={rtspUrl}
                      onChange={(e) => setRtspUrl(e.target.value)}
                    />
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Enter the RTSP stream URL of your IP camera
                    </span>
                  </div>
                )}
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => { setShowModal(false); resetForm(); }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Adding...' : '+ Add Camera'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
