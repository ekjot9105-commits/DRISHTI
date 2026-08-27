/**
 * CameraManagement — Add, configure, start/stop, and delete camera sources.
 * Styled with Tailwind CSS matching the Zenith Sentinel Design System.
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
    if (!window.confirm('Are you sure you want to delete this camera?')) return;
    try {
      await deleteCamera(cameraId);
      onCamerasChange();
    } catch (err) {
      console.error('Failed to delete camera:', err);
    }
  };

  return (
    <div className="p-margin-page flex-1 flex flex-col h-full bg-surface relative">
      {/* Background pattern */}
      <div className="absolute inset-0 pointer-events-none opacity-5" style={{backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '20px 20px'}}></div>
      
      {/* Page header */}
      <div className="flex justify-between items-center mb-6 relative z-10">
        <div>
          <h2 className="font-headline-md text-on-surface">Camera Management</h2>
          <p className="font-body-md text-on-surface-variant">Configure and manage surveillance camera sources</p>
        </div>
        <button className="bg-primary/20 text-primary border border-primary/50 hover:bg-primary/30 px-4 py-2 rounded-sm font-label-caps flex items-center transition-colors" onClick={() => setShowModal(true)}>
          <span className="material-symbols-outlined mr-2 text-[18px]">add</span> ADD CAMERA
        </button>
      </div>

      {/* Camera cards */}
      <div className="flex-1 relative z-10 overflow-y-auto">
        {cameras.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center bg-surface-container-low border border-outline-variant/30 rounded-sm py-24">
            <span className="material-symbols-outlined text-5xl mb-4 text-on-surface-variant opacity-50" style={{fontVariationSettings: "'FILL' 1"}}>videocam_off</span>
            <span className="font-label-caps text-on-surface text-lg">No cameras configured</span>
            <span className="font-body-md text-on-surface-variant text-sm mt-2">Add your first camera to start monitoring</span>
            <button className="mt-6 bg-primary/20 text-primary border border-primary/50 hover:bg-primary/30 px-6 py-2.5 rounded-sm font-label-caps transition-colors flex items-center" onClick={() => setShowModal(true)}>
              <span className="material-symbols-outlined mr-2 text-[16px]">add</span>
              ADD CAMERA
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-gutter">
            {cameras.map((camera) => (
              <div key={camera.id} className="bg-surface-container-low border border-outline-variant/50 rounded-sm flex flex-col group overflow-hidden">
                <div className="p-3 border-b border-outline-variant/30 bg-surface/50 flex justify-between items-center">
                  <span className="font-label-caps text-on-surface tracking-widest truncate max-w-[150px]">{camera.name}</span>
                  <span className={`px-2 py-0.5 rounded-sm font-label-caps text-[9px] flex items-center border ${camera.status === 'active' ? 'bg-primary/20 text-primary border-primary/50' : 'bg-surface-container text-on-surface-variant border-outline-variant'}`}>
                    {camera.status === 'active' && <span className="w-1.5 h-1.5 rounded-full bg-primary mr-1 animate-pulse"></span>}
                    {camera.status === 'active' ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>
                
                <div className="p-4 flex flex-col space-y-3 flex-1">
                  <div className="flex items-center text-on-surface-variant text-xs font-body-md">
                    <span className="material-symbols-outlined mr-2 text-[16px]">{camera.source_type === 'file' ? 'folder' : 'router'}</span>
                    {camera.source_type === 'file' ? 'Video File' : 'RTSP Stream'}
                  </div>
                  {camera.location && (
                    <div className="flex items-center text-on-surface-variant text-xs font-body-md">
                      <span className="material-symbols-outlined mr-2 text-[16px]">location_on</span>
                      {camera.location}
                    </div>
                  )}
                  
                  <div className="pt-4 border-t border-outline-variant/30 flex space-x-2 mt-auto">
                    {camera.status === 'active' ? (
                      <button className="flex-1 bg-surface-container hover:bg-surface-container-high text-on-surface border border-outline-variant/50 py-1.5 rounded-sm font-label-caps text-[10px] transition-colors flex items-center justify-center" onClick={() => handleStop(camera.id)}>
                        <span className="material-symbols-outlined mr-1 text-[12px]" style={{fontVariationSettings: "'FILL' 1"}}>stop_circle</span> STOP
                      </button>
                    ) : (
                      <button className="flex-1 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/50 py-1.5 rounded-sm font-label-caps text-[10px] transition-colors flex items-center justify-center" onClick={() => handleStart(camera.id)}>
                        <span className="material-symbols-outlined mr-1 text-[12px]" style={{fontVariationSettings: "'FILL' 1"}}>play_circle</span> START
                      </button>
                    )}
                    <button className="flex-1 bg-error/10 hover:bg-error/20 text-error border border-error/30 py-1.5 rounded-sm font-label-caps text-[10px] transition-colors flex items-center justify-center" onClick={() => handleDelete(camera.id)}>
                      <span className="material-symbols-outlined mr-1 text-[12px]">delete</span> DELETE
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Camera Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container-low border border-outline-variant/50 rounded-sm w-full max-w-md shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b border-outline-variant/30 flex justify-between items-center bg-surface/50">
              <h3 className="font-headline-sm text-on-surface">Add Camera Source</h3>
              <button className="text-on-surface-variant hover:text-on-surface transition-colors" onClick={() => { setShowModal(false); resetForm(); }}>
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-5 flex flex-col space-y-5">
              {error && (
                <div className="bg-error/10 border border-error/30 text-error px-3 py-2 rounded-sm text-sm font-body-md flex items-center">
                  <span className="material-symbols-outlined mr-2 text-[18px]">error</span>
                  {error}
                </div>
              )}

              <div className="flex flex-col space-y-1">
                <label className="font-label-caps text-on-surface-variant text-[10px]">CAMERA NAME</label>
                <input type="text" className="bg-surface border border-outline-variant/50 text-on-surface text-sm rounded-sm px-3 py-2.5 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all" value={name} onChange={e => setName(e.target.value)} required placeholder="e.g. Sector 7 North Gate" />
              </div>

              <div className="flex flex-col space-y-1">
                <label className="font-label-caps text-on-surface-variant text-[10px]">LOCATION (OPTIONAL)</label>
                <input type="text" className="bg-surface border border-outline-variant/50 text-on-surface text-sm rounded-sm px-3 py-2.5 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all" value={location} onChange={e => setLocation(e.target.value)} placeholder="e.g. North Gate" />
              </div>

              <div className="flex flex-col space-y-1">
                <label className="font-label-caps text-on-surface-variant text-[10px]">SOURCE TYPE</label>
                <div className="flex bg-surface-container rounded-sm p-1">
                  <button type="button" className={`flex-1 py-2 text-xs font-label-caps rounded-sm transition-colors flex items-center justify-center ${sourceType === 'file' ? 'bg-primary/20 text-primary border border-primary/30' : 'text-on-surface-variant hover:text-on-surface'}`} onClick={() => setSourceType('file')}>
                    <span className="material-symbols-outlined mr-1 text-[16px]">folder</span> VIDEO FILE
                  </button>
                  <button type="button" className={`flex-1 py-2 text-xs font-label-caps rounded-sm transition-colors flex items-center justify-center ${sourceType === 'rtsp' ? 'bg-primary/20 text-primary border border-primary/30' : 'text-on-surface-variant hover:text-on-surface'}`} onClick={() => setSourceType('rtsp')}>
                    <span className="material-symbols-outlined mr-1 text-[16px]">router</span> RTSP STREAM
                  </button>
                </div>
              </div>

              {sourceType === 'file' ? (
                <div className="flex flex-col space-y-1">
                  <label className="font-label-caps text-on-surface-variant text-[10px]">VIDEO FILE</label>
                  <div className="border border-dashed border-outline-variant hover:border-primary/50 bg-surface/50 rounded-sm p-6 flex flex-col items-center justify-center cursor-pointer transition-colors" onClick={() => fileInputRef.current?.click()}>
                    <span className="material-symbols-outlined text-on-surface-variant mb-2 text-3xl">upload_file</span>
                    <span className="text-sm font-body-md text-on-surface text-center px-4">{videoFile ? videoFile.name : 'Click to select video file'}</span>
                    <span className="text-[10px] font-label-md text-on-surface-variant mt-2">Supported: MP4, AVI, MKV, MOV</span>
                  </div>
                  <input ref={fileInputRef} type="file" accept="video/*" className="hidden" onChange={e => setVideoFile(e.target.files[0])} />
                </div>
              ) : (
                <div className="flex flex-col space-y-1">
                  <label className="font-label-caps text-on-surface-variant text-[10px]">RTSP URL</label>
                  <input type="text" className="bg-surface border border-outline-variant/50 text-on-surface text-sm rounded-sm px-3 py-2.5 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all" value={rtspUrl} onChange={e => setRtspUrl(e.target.value)} placeholder="rtsp://username:password@192.168.1.100:554/stream" />
                </div>
              )}

              <div className="pt-2 flex space-x-3 justify-end">
                <button type="button" className="px-4 py-2 font-label-caps text-[11px] text-on-surface-variant hover:text-on-surface transition-colors" onClick={() => { setShowModal(false); resetForm(); }}>CANCEL</button>
                <button type="submit" disabled={loading} className="bg-primary hover:bg-primary/90 text-on-primary px-5 py-2 rounded-sm font-label-caps text-[11px] transition-colors flex items-center">
                  {loading ? (
                    <><span className="material-symbols-outlined mr-2 text-[14px] animate-spin">refresh</span> ADDING...</>
                  ) : (
                    <><span className="material-symbols-outlined mr-2 text-[14px]">add</span> ADD CAMERA</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
